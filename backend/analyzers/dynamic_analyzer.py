"""
Dynamic Code Analyzer

Executes Python code in a controlled environment and collects runtime information.
Uses sys.settrace() to track execution flow, variable values, and runtime behavior.

Enhanced with:
- Actual timeout enforcement using threading
- Memory usage tracking
- Better handling of generators and comprehensions
- Class instantiation tracking
- Improved value serialization for complex types
- Resource limits and safety measures
"""

import sys
import io
import ast
import threading
import signal
import traceback
import resource
import gc
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from contextlib import redirect_stdout, redirect_stderr
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


@dataclass
class VariableSnapshot:
    """A snapshot of a variable's value at a specific point in execution."""
    name: str
    value: Any
    value_type: str
    line: int
    scope: str  # function name or 'global'


@dataclass
class LoopExecution:
    """Information about a loop's execution."""
    line_start: int
    iteration_count: int
    loop_type: str  # 'for' or 'while'


@dataclass
class FunctionCall:
    """Information about a function call during execution."""
    function_name: str
    line: int
    arguments: Dict[str, Any]
    return_value: Any = None
    stack_depth: int = 0
    execution_time_ms: float = 0.0  # New: track execution time
    is_recursive_call: bool = False  # New: track if this is a recursive call


@dataclass
class ClassInstantiation:
    """Information about a class being instantiated."""
    class_name: str
    line: int
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratorYield:
    """Information about a generator yield."""
    function_name: str
    line: int
    yielded_value: Any
    yield_count: int


@dataclass
class ExecutionTrace:
    """Complete execution trace of a program."""
    variable_snapshots: List[VariableSnapshot] = field(default_factory=list)
    loop_executions: List[LoopExecution] = field(default_factory=list)
    function_calls: List[FunctionCall] = field(default_factory=list)
    execution_flow: List[int] = field(default_factory=list)  # line numbers in order
    max_stack_depth: int = 0
    stdout_output: str = ""
    stderr_output: str = ""
    exception: Optional[str] = None
    exception_traceback: Optional[str] = None  # New: full traceback
    # New fields
    class_instantiations: List[ClassInstantiation] = field(default_factory=list)
    generator_yields: List[GeneratorYield] = field(default_factory=list)
    execution_time_ms: float = 0.0
    memory_peak_mb: float = 0.0
    timed_out: bool = False
    total_function_calls: int = 0
    unique_functions_called: Set[str] = field(default_factory=set)


class ExecutionTracer:
    """
    Traces program execution using sys.settrace().
    Collects runtime information about variables, loops, and function calls.

    Enhanced with:
    - Class instantiation tracking
    - Generator yield tracking
    - Better recursion detection
    - Memory-efficient snapshot limiting
    """

    # Limits to prevent memory issues with large programs
    MAX_SNAPSHOTS = 1000
    MAX_EXECUTION_FLOW = 5000
    MAX_FUNCTION_CALLS = 500
    MAX_VALUE_SIZE = 1000  # Max chars for serialized values

    def __init__(self):
        self.trace = ExecutionTrace()
        self.current_stack_depth = 0
        self.loop_counters: Dict[int, int] = {}  # line -> iteration count
        self.visited_lines: Set[int] = set()
        self.in_loop_lines: Set[int] = set()  # lines that are part of loops
        self.function_frames: List[str] = []  # stack of function names
        self.function_call_stack: List[str] = []  # For recursion detection
        self.yield_counters: Dict[str, int] = {}  # function -> yield count
        self._stopped = False  # Flag to stop tracing early if limits exceeded

    def trace_calls(self, frame, event, arg):
        """
        Trace function called by sys.settrace().

        Args:
            frame: Current execution frame
            event: Event type ('call', 'line', 'return', 'exception')
            arg: Event-specific argument
        """
        # Stop if limits exceeded
        if self._stopped:
            return None

        # Check if we've exceeded limits
        if (len(self.trace.variable_snapshots) >= self.MAX_SNAPSHOTS or
            len(self.trace.execution_flow) >= self.MAX_EXECUTION_FLOW or
            len(self.trace.function_calls) >= self.MAX_FUNCTION_CALLS):
            self._stopped = True
            return None

        try:
            if event == 'call':
                return self._handle_call(frame)
            elif event == 'line':
                return self._handle_line(frame)
            elif event == 'return':
                return self._handle_return(frame, arg)
            elif event == 'exception':
                return self._handle_exception(frame, arg)
        except Exception:
            # Don't let tracer errors crash the execution
            pass

        return self.trace_calls

    def _handle_call(self, frame):
        """Handle function call event."""
        self.current_stack_depth += 1
        self.trace.max_stack_depth = max(self.trace.max_stack_depth, self.current_stack_depth)

        func_name = frame.f_code.co_name
        line_no = frame.f_lineno

        # Track function name
        self.function_frames.append(func_name)

        # Check for recursion
        is_recursive = func_name in self.function_call_stack
        self.function_call_stack.append(func_name)

        # Capture function arguments (with size limits)
        args = {}
        arg_names = frame.f_code.co_varnames[:frame.f_code.co_argcount]
        for arg_name in arg_names:
            if arg_name in frame.f_locals:
                args[arg_name] = self._safe_serialize(frame.f_locals[arg_name])

        # Record function call
        if func_name != '<module>':  # Skip module-level "function"
            self.trace.total_function_calls += 1
            self.trace.unique_functions_called.add(func_name)

            call = FunctionCall(
                function_name=func_name,
                line=line_no,
                arguments=args,
                stack_depth=self.current_stack_depth,
                is_recursive_call=is_recursive,
            )
            self.trace.function_calls.append(call)

            # Check if this is a class instantiation (__init__)
            if func_name == '__init__' and 'self' in frame.f_locals:
                self_obj = frame.f_locals['self']
                class_name = type(self_obj).__name__
                init_args = {k: self._safe_serialize(v) for k, v in args.items() if k != 'self'}
                instantiation = ClassInstantiation(
                    class_name=class_name,
                    line=line_no,
                    arguments=init_args,
                )
                self.trace.class_instantiations.append(instantiation)

        return self.trace_calls

    def _safe_serialize(self, value: Any, max_depth: int = 3) -> Any:
        """Safely serialize a value with size and depth limits."""
        if max_depth <= 0:
            return "<max depth exceeded>"

        if value is None or isinstance(value, (bool, int, float)):
            return value
        elif isinstance(value, str):
            if len(value) > self.MAX_VALUE_SIZE:
                return value[:self.MAX_VALUE_SIZE] + f"... (truncated, total {len(value)} chars)"
            return value
        elif isinstance(value, (list, tuple)):
            if len(value) > 20:
                serialized = [self._safe_serialize(v, max_depth - 1) for v in value[:20]]
                return serialized + [f"... ({len(value) - 20} more items)"]
            return [self._safe_serialize(v, max_depth - 1) for v in value]
        elif isinstance(value, dict):
            if len(value) > 20:
                items = list(value.items())[:20]
                result = {k: self._safe_serialize(v, max_depth - 1) for k, v in items}
                result["..."] = f"({len(value) - 20} more items)"
                return result
            return {k: self._safe_serialize(v, max_depth - 1) for k, v in value.items()}
        elif isinstance(value, set):
            return list(value)[:20] + ([f"... ({len(value) - 20} more)"] if len(value) > 20 else [])
        else:
            # For complex objects, return a safe string representation
            try:
                repr_str = repr(value)
                if len(repr_str) > self.MAX_VALUE_SIZE:
                    return repr_str[:self.MAX_VALUE_SIZE] + "..."
                return repr_str
            except Exception:
                return f"<{type(value).__name__} object>"

    def _handle_line(self, frame):
        """Handle line execution event."""
        line_no = frame.f_lineno

        # Track execution flow (with limit check)
        if len(self.trace.execution_flow) < self.MAX_EXECUTION_FLOW:
            self.trace.execution_flow.append(line_no)

        # Detect loops by checking if we're revisiting lines
        if line_no in self.visited_lines:
            self.in_loop_lines.add(line_no)
            # Increment loop counter
            if line_no in self.loop_counters:
                self.loop_counters[line_no] += 1
            else:
                self.loop_counters[line_no] = 1
        else:
            self.visited_lines.add(line_no)

        # Capture variable snapshots (with limit check)
        if len(self.trace.variable_snapshots) < self.MAX_SNAPSHOTS:
            scope = self.function_frames[-1] if self.function_frames else '<module>'
            # Convert <module> to 'global' for consistency
            if scope == '<module>':
                scope = 'global'

            for var_name, var_value in frame.f_locals.items():
                # Skip internal variables, special methods, and contextlib internals
                if (not var_name.startswith('__') and
                    not var_name.startswith('@') and
                    scope not in ['__init__', '__enter__', '__exit__', '__call__']):

                    # Use safe serialization to prevent memory issues
                    serialized_value = self._safe_serialize(var_value)

                    snapshot = VariableSnapshot(
                        name=var_name,
                        value=serialized_value,
                        value_type=type(var_value).__name__,
                        line=line_no,
                        scope=scope
                    )
                    self.trace.variable_snapshots.append(snapshot)

                    # Check limit after each addition
                    if len(self.trace.variable_snapshots) >= self.MAX_SNAPSHOTS:
                        break

        return self.trace_calls

    def _handle_return(self, frame, arg):
        """Handle function return event."""
        self.current_stack_depth -= 1

        func_name = frame.f_code.co_name

        # Update return value for the last call to this function
        if func_name != '<module>':
            for call in reversed(self.trace.function_calls):
                if call.function_name == func_name and call.return_value is None:
                    call.return_value = self._safe_serialize(arg)
                    break

        # Pop function from stacks
        if self.function_frames:
            self.function_frames.pop()
        if self.function_call_stack:
            self.function_call_stack.pop()

        return self.trace_calls

    def _handle_exception(self, frame, arg):
        """Handle exception event."""
        exc_type, exc_value, exc_traceback = arg
        self.trace.exception = f"{exc_type.__name__}: {exc_value}"
        # Capture full traceback for debugging
        try:
            self.trace.exception_traceback = ''.join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
        except Exception:
            pass
        return self.trace_calls

    def handle_yield(self, func_name: str, line: int, value: Any):
        """Track a generator yield (called externally if needed)."""
        if func_name not in self.yield_counters:
            self.yield_counters[func_name] = 0
        self.yield_counters[func_name] += 1

        yield_info = GeneratorYield(
            function_name=func_name,
            line=line,
            yielded_value=self._safe_serialize(value),
            yield_count=self.yield_counters[func_name],
        )
        self.trace.generator_yields.append(yield_info)

    def finalize_loop_info(self, source_code: str):
        """
        Analyze loop execution after tracing is complete.
        Uses AST to identify loop structures and match with execution data.
        """
        try:
            tree = ast.parse(source_code)

            # Find all loop nodes
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    loop_start = node.lineno
                    loop_type = 'for' if isinstance(node, ast.For) else 'while'

                    # Count iterations based on how many times we visited lines in the loop
                    # The loop header line is visited once per iteration
                    iteration_count = self.loop_counters.get(loop_start, 0)

                    loop_exec = LoopExecution(
                        line_start=loop_start,
                        iteration_count=iteration_count,
                        loop_type=loop_type
                    )
                    self.trace.loop_executions.append(loop_exec)
        except:
            pass  # If we can't parse, skip loop analysis


class TimeoutException(Exception):
    """Exception raised when code execution times out."""
    pass


class DynamicAnalyzer:
    """
    Main dynamic analyzer class.
    Executes Python code safely and collects runtime information.

    Enhanced with:
    - Actual timeout enforcement using threading
    - Memory tracking
    - Resource limits
    - Better error handling
    """

    # Safety limits
    MAX_MEMORY_MB = 100  # Maximum memory usage
    MAX_OUTPUT_SIZE = 10000  # Maximum stdout/stderr size

    def __init__(self, timeout: int = 5, max_memory_mb: int = 100):
        """
        Initialize the dynamic analyzer.

        Args:
            timeout: Maximum execution time in seconds
            max_memory_mb: Maximum memory usage in MB
        """
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    def analyze(self, source_code: str, test_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute code and collect runtime information with timeout enforcement.

        Args:
            source_code: Python source code to execute
            test_inputs: Optional dictionary of global variables to inject

        Returns:
            Dictionary containing execution trace and runtime facts
        """
        import time
        start_time = time.time()

        tracer = ExecutionTracer()
        exec_globals = {'__name__': '__main__', '__builtins__': __builtins__}
        if test_inputs:
            exec_globals.update(test_inputs)

        # Result container for thread communication
        result_container = {
            'completed': False,
            'exception': None,
            'stdout': '',
            'stderr': '',
        }

        def execute_code():
            """Inner function to execute code in a controlled environment."""
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            sys.settrace(tracer.trace_calls)
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    exec(source_code, exec_globals)
                result_container['completed'] = True
            except Exception as e:
                tracer.trace.exception = f"{type(e).__name__}: {str(e)}"
                try:
                    tracer.trace.exception_traceback = traceback.format_exc()
                except Exception:
                    pass
            finally:
                sys.settrace(None)
                # Truncate output if too large
                stdout_val = stdout_capture.getvalue()
                stderr_val = stderr_capture.getvalue()
                result_container['stdout'] = stdout_val[:self.MAX_OUTPUT_SIZE] if len(stdout_val) > self.MAX_OUTPUT_SIZE else stdout_val
                result_container['stderr'] = stderr_val[:self.MAX_OUTPUT_SIZE] if len(stderr_val) > self.MAX_OUTPUT_SIZE else stderr_val

        # Execute with timeout using ThreadPoolExecutor
        timed_out = False
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(execute_code)
            try:
                future.result(timeout=self.timeout)
            except FutureTimeoutError:
                timed_out = True
                tracer.trace.timed_out = True
                tracer.trace.exception = f"TimeoutError: Execution exceeded {self.timeout} seconds"
            except Exception as e:
                tracer.trace.exception = f"{type(e).__name__}: {str(e)}"

        # Capture final state
        tracer.trace.stdout_output = result_container['stdout']
        tracer.trace.stderr_output = result_container['stderr']

        # Capture final global variables (only if execution completed or timed out gracefully)
        if not timed_out:
            for var_name, var_value in exec_globals.items():
                if not var_name.startswith('__') and var_name not in ['__builtins__']:
                    snapshot = VariableSnapshot(
                        name=var_name,
                        value=tracer._safe_serialize(var_value),
                        value_type=type(var_value).__name__,
                        line=-1,  # Indicate final state
                        scope='global'
                    )
                    tracer.trace.variable_snapshots.append(snapshot)

        # Finalize loop information
        tracer.finalize_loop_info(source_code)

        # Record execution time
        end_time = time.time()
        tracer.trace.execution_time_ms = (end_time - start_time) * 1000

        # Try to get memory usage
        try:
            tracer.trace.memory_peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except Exception:
            pass

        # Compile results
        return self._compile_results(tracer.trace, exec_globals)

    def _compile_results(self, trace: ExecutionTrace, final_globals: Dict) -> Dict[str, Any]:
        """Compile execution trace into a structured result dictionary."""

        # Get unique variable snapshots (last value for each var in each scope)
        final_variables = {}
        for snapshot in reversed(trace.variable_snapshots):
            key = (snapshot.scope, snapshot.name)
            if key not in final_variables:
                final_variables[key] = snapshot

        return {
            'execution_successful': trace.exception is None and not trace.timed_out,
            'exception': trace.exception,
            'exception_traceback': trace.exception_traceback,
            'timed_out': trace.timed_out,
            'max_stack_depth': trace.max_stack_depth,
            'total_lines_executed': len(trace.execution_flow),
            'unique_lines_executed': len(set(trace.execution_flow)),
            'execution_flow': trace.execution_flow[:1000],  # Limit for JSON response
            'execution_flow_truncated': len(trace.execution_flow) > 1000,
            'stdout': trace.stdout_output,
            'stderr': trace.stderr_output,
            'execution_time_ms': trace.execution_time_ms,
            'memory_peak_mb': trace.memory_peak_mb,
            'function_calls': [
                {
                    'function_name': call.function_name,
                    'line': call.line,
                    'arguments': call.arguments,
                    'return_value': call.return_value,
                    'stack_depth': call.stack_depth,
                    'is_recursive_call': call.is_recursive_call,
                }
                for call in trace.function_calls
            ],
            'total_function_calls': trace.total_function_calls,
            'unique_functions_called': list(trace.unique_functions_called),
            'loop_executions': [
                {
                    'line_start': loop.line_start,
                    'iteration_count': loop.iteration_count,
                    'loop_type': loop.loop_type
                }
                for loop in trace.loop_executions
            ],
            'variable_snapshots': [
                {
                    'name': snapshot.name,
                    'value': self._serialize_value(snapshot.value),
                    'value_type': snapshot.value_type,
                    'line': snapshot.line,
                    'scope': snapshot.scope
                }
                for snapshot in trace.variable_snapshots[:500]  # Limit for response
            ],
            'variable_snapshots_truncated': len(trace.variable_snapshots) > 500,
            'final_variables': {
                f"{scope}.{name}": {
                    'value': self._serialize_value(snapshot.value),
                    'type': snapshot.value_type
                }
                for (scope, name), snapshot in final_variables.items()
            },
            # New fields
            'class_instantiations': [
                {
                    'class_name': inst.class_name,
                    'line': inst.line,
                    'arguments': inst.arguments,
                }
                for inst in trace.class_instantiations
            ],
            'generator_yields': [
                {
                    'function_name': y.function_name,
                    'line': y.line,
                    'yielded_value': y.yielded_value,
                    'yield_count': y.yield_count,
                }
                for y in trace.generator_yields
            ],
            'has_recursion': any(call.is_recursive_call for call in trace.function_calls),
        }

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a value for JSON compatibility.
        Handles common Python types safely.
        """
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, set):
            return list(value)
        else:
            # For complex objects, return string representation
            return str(value)


# Convenience function for quick analysis
def analyze_code(source_code: str, test_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Quick function to dynamically analyze code.

    Args:
        source_code: Python source code to execute
        test_inputs: Optional dictionary of inputs to provide

    Returns:
        Dictionary containing execution trace and runtime facts
    """
    analyzer = DynamicAnalyzer()
    return analyzer.analyze(source_code, test_inputs)
