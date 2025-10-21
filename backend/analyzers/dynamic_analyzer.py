"""
Dynamic Code Analyzer

Executes Python code in a controlled environment and collects runtime information.
Uses sys.settrace() to track execution flow, variable values, and runtime behavior.
"""

import sys
import io
import ast
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from contextlib import redirect_stdout, redirect_stderr


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


class ExecutionTracer:
    """
    Traces program execution using sys.settrace().
    Collects runtime information about variables, loops, and function calls.
    """

    def __init__(self):
        self.trace = ExecutionTrace()
        self.current_stack_depth = 0
        self.loop_counters: Dict[int, int] = {}  # line -> iteration count
        self.visited_lines: Set[int] = set()
        self.in_loop_lines: Set[int] = set()  # lines that are part of loops
        self.function_frames: List[str] = []  # stack of function names

    def trace_calls(self, frame, event, arg):
        """
        Trace function called by sys.settrace().

        Args:
            frame: Current execution frame
            event: Event type ('call', 'line', 'return', 'exception')
            arg: Event-specific argument
        """
        if event == 'call':
            return self._handle_call(frame)
        elif event == 'line':
            return self._handle_line(frame)
        elif event == 'return':
            return self._handle_return(frame, arg)
        elif event == 'exception':
            return self._handle_exception(frame, arg)

        return self.trace_calls

    def _handle_call(self, frame):
        """Handle function call event."""
        self.current_stack_depth += 1
        self.trace.max_stack_depth = max(self.trace.max_stack_depth, self.current_stack_depth)

        func_name = frame.f_code.co_name
        line_no = frame.f_lineno

        # Track function name
        self.function_frames.append(func_name)

        # Capture function arguments
        args = {}
        arg_names = frame.f_code.co_varnames[:frame.f_code.co_argcount]
        for arg_name in arg_names:
            if arg_name in frame.f_locals:
                args[arg_name] = frame.f_locals[arg_name]

        # Record function call
        if func_name != '<module>':  # Skip module-level "function"
            call = FunctionCall(
                function_name=func_name,
                line=line_no,
                arguments=args,
                stack_depth=self.current_stack_depth
            )
            self.trace.function_calls.append(call)

        return self.trace_calls

    def _handle_line(self, frame):
        """Handle line execution event."""
        line_no = frame.f_lineno

        # Track execution flow
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

        # Capture variable snapshots
        scope = self.function_frames[-1] if self.function_frames else '<module>'
        # Convert <module> to 'global' for consistency
        if scope == '<module>':
            scope = 'global'

        for var_name, var_value in frame.f_locals.items():
            # Skip internal variables, special methods, and contextlib internals
            if (not var_name.startswith('__') and
                scope not in ['__init__', '__enter__', '__exit__', '__call__']):
                snapshot = VariableSnapshot(
                    name=var_name,
                    value=var_value,
                    value_type=type(var_value).__name__,
                    line=line_no,
                    scope=scope
                )
                self.trace.variable_snapshots.append(snapshot)

        return self.trace_calls

    def _handle_return(self, frame, arg):
        """Handle function return event."""
        self.current_stack_depth -= 1

        func_name = frame.f_code.co_name

        # Update return value for the last call to this function
        if func_name != '<module>':
            for call in reversed(self.trace.function_calls):
                if call.function_name == func_name and call.return_value is None:
                    call.return_value = arg
                    break

        # Pop function from stack
        if self.function_frames:
            self.function_frames.pop()

        return self.trace_calls

    def _handle_exception(self, frame, arg):
        """Handle exception event."""
        exc_type, exc_value, exc_traceback = arg
        self.trace.exception = f"{exc_type.__name__}: {exc_value}"
        return self.trace_calls

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


class DynamicAnalyzer:
    """
    Main dynamic analyzer class.
    Executes Python code safely and collects runtime information.
    """

    def __init__(self, timeout: int = 5):
        """
        Initialize the dynamic analyzer.

        Args:
            timeout: Maximum execution time in seconds (not yet implemented)
        """
        self.timeout = timeout

    def analyze(self, source_code: str, test_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute code and collect runtime information.

        Args:
            source_code: Python source code to execute
            test_inputs: Optional dictionary of global variables to inject

        Returns:
            Dictionary containing execution trace and runtime facts
        """
        tracer = ExecutionTracer()

        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Create execution namespace
        exec_globals = {'__name__': '__main__', '__builtins__': __builtins__}
        if test_inputs:
            exec_globals.update(test_inputs)

        # Set up tracing
        sys.settrace(tracer.trace_calls)

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the code
                exec(source_code, exec_globals)
        except Exception as e:
            tracer.trace.exception = f"{type(e).__name__}: {str(e)}"
        finally:
            # Disable tracing
            sys.settrace(None)

            # Capture final global variables from exec_globals
            for var_name, var_value in exec_globals.items():
                if not var_name.startswith('__') and var_name not in ['__builtins__']:
                    snapshot = VariableSnapshot(
                        name=var_name,
                        value=var_value,
                        value_type=type(var_value).__name__,
                        line=-1,  # Indicate final state
                        scope='global'
                    )
                    tracer.trace.variable_snapshots.append(snapshot)

            # Capture output
            tracer.trace.stdout_output = stdout_capture.getvalue()
            tracer.trace.stderr_output = stderr_capture.getvalue()

            # Finalize loop information
            tracer.finalize_loop_info(source_code)

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
            'execution_successful': trace.exception is None,
            'exception': trace.exception,
            'max_stack_depth': trace.max_stack_depth,
            'total_lines_executed': len(trace.execution_flow),
            'unique_lines_executed': len(set(trace.execution_flow)),
            'execution_flow': trace.execution_flow,
            'stdout': trace.stdout_output,
            'stderr': trace.stderr_output,
            'function_calls': [
                {
                    'function_name': call.function_name,
                    'line': call.line,
                    'arguments': call.arguments,
                    'return_value': call.return_value,
                    'stack_depth': call.stack_depth
                }
                for call in trace.function_calls
            ],
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
                for snapshot in trace.variable_snapshots
            ],
            'final_variables': {
                f"{scope}.{name}": {
                    'value': self._serialize_value(snapshot.value),
                    'type': snapshot.value_type
                }
                for (scope, name), snapshot in final_variables.items()
            }
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
