"""
Static Code Analyzer

Analyzes Python source code without executing it.
Extracts structural information using AST (Abstract Syntax Tree).
"""

import ast
from typing import Dict, List, Any, Set
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    params: List[str]
    line_start: int
    line_end: int
    is_recursive: bool = False
    has_conditionals: bool = False
    has_loops: bool = False
    return_count: int = 0
    calls_functions: List[str] = field(default_factory=list)


@dataclass
class VariableInfo:
    """Information about a variable."""
    name: str
    line: int
    scope: str  # 'global' or function name


@dataclass
class LoopInfo:
    """Information about a loop."""
    type: str  # 'for' or 'while'
    line_start: int
    line_end: int
    loop_variable: str = None  # For 'for' loops
    nesting_level: int = 0


@dataclass
class ConditionalInfo:
    """Information about an if statement."""
    type: str  # 'if'
    line: int
    has_elif: bool = False
    has_else: bool = False


@dataclass
class FunctionCallInfo:
    """Information about a function call."""
    function: str
    line: int
    arguments_count: int


class CodeVisitor(ast.NodeVisitor):
    """
    Custom AST visitor to extract code facts.
    Walks through the AST and collects information about code structures.
    """

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.functions: List[FunctionInfo] = []
        self.variables: List[VariableInfo] = []
        self.loops: List[LoopInfo] = []
        self.conditionals: List[ConditionalInfo] = []
        self.function_calls: List[FunctionCallInfo] = []

        # Tracking context
        self.current_function: str = None
        self.loop_depth: int = 0
        self.function_names: Set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit a function definition."""
        # Store function name for later reference
        self.function_names.add(node.name)

        # Extract parameters
        params = [arg.arg for arg in node.args.args]

        # Create function info
        func_info = FunctionInfo(
            name=node.name,
            params=params,
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        )

        # Set current function context
        prev_function = self.current_function
        self.current_function = node.name

        # Check for recursion, conditionals, loops, returns
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Check if function calls itself
                if isinstance(child.func, ast.Name) and child.func.id == node.name:
                    func_info.is_recursive = True

            elif isinstance(child, ast.If):
                func_info.has_conditionals = True

            elif isinstance(child, (ast.For, ast.While)):
                func_info.has_loops = True

            elif isinstance(child, ast.Return):
                func_info.return_count += 1

        # Collect function calls within this function
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id not in func_info.calls_functions:
                    func_info.calls_functions.append(child.func.id)

        self.functions.append(func_info)

        # Continue visiting children
        self.generic_visit(node)

        # Restore previous function context
        self.current_function = prev_function

    def visit_Assign(self, node: ast.Assign):
        """Visit an assignment statement to track variables."""
        scope = self.current_function if self.current_function else 'global'

        for target in node.targets:
            if isinstance(target, ast.Name):
                var_info = VariableInfo(
                    name=target.id,
                    line=node.lineno,
                    scope=scope
                )
                self.variables.append(var_info)

        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        """Visit a for loop."""
        loop_var = None
        if isinstance(node.target, ast.Name):
            loop_var = node.target.id

        loop_info = LoopInfo(
            type='for',
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            loop_variable=loop_var,
            nesting_level=self.loop_depth
        )
        self.loops.append(loop_info)

        # Increase loop depth for nested loops
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node: ast.While):
        """Visit a while loop."""
        loop_info = LoopInfo(
            type='while',
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            nesting_level=self.loop_depth
        )
        self.loops.append(loop_info)

        # Increase loop depth for nested loops
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_If(self, node: ast.If):
        """Visit an if statement."""
        has_elif = False
        has_else = False

        # Check for elif
        if node.orelse:
            if isinstance(node.orelse[0], ast.If):
                has_elif = True
            else:
                has_else = True

        cond_info = ConditionalInfo(
            type='if',
            line=node.lineno,
            has_elif=has_elif,
            has_else=has_else
        )
        self.conditionals.append(cond_info)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Visit a function call."""
        func_name = None

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name:
            call_info = FunctionCallInfo(
                function=func_name,
                line=node.lineno,
                arguments_count=len(node.args)
            )
            self.function_calls.append(call_info)

        self.generic_visit(node)


class StaticAnalyzer:
    """
    Main static analyzer class.
    Analyzes Python source code and extracts structural information.
    """

    def analyze(self, source_code: str) -> Dict[str, Any]:
        """
        Analyze Python source code and return extracted facts.

        Args:
            source_code: Python source code as a string

        Returns:
            Dictionary containing extracted code facts

        Raises:
            SyntaxError: If the code has syntax errors
        """
        try:
            # Parse the source code into an AST
            tree = ast.parse(source_code)

            # Split source into lines for reference
            source_lines = source_code.split('\n')

            # Create visitor and walk the tree
            visitor = CodeVisitor(source_lines)
            visitor.visit(tree)

            # Compile results
            results = {
                'functions': [self._function_to_dict(f) for f in visitor.functions],
                'variables': [self._variable_to_dict(v) for v in visitor.variables],
                'loops': [self._loop_to_dict(l) for l in visitor.loops],
                'conditionals': [self._conditional_to_dict(c) for c in visitor.conditionals],
                'function_calls': [self._call_to_dict(c) for c in visitor.function_calls],
                'summary': {
                    'total_functions': len(visitor.functions),
                    'total_variables': len(visitor.variables),
                    'total_loops': len(visitor.loops),
                    'total_conditionals': len(visitor.conditionals),
                    'has_recursion': any(f.is_recursive for f in visitor.functions),
                    'total_lines': len(source_lines)
                }
            }

            return results

        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in code: {e}")

    @staticmethod
    def _function_to_dict(func: FunctionInfo) -> Dict:
        """Convert FunctionInfo to dictionary."""
        return {
            'name': func.name,
            'params': func.params,
            'param_count': len(func.params),
            'line_start': func.line_start,
            'line_end': func.line_end,
            'is_recursive': func.is_recursive,
            'has_conditionals': func.has_conditionals,
            'has_loops': func.has_loops,
            'return_count': func.return_count,
            'calls_functions': func.calls_functions
        }

    @staticmethod
    def _variable_to_dict(var: VariableInfo) -> Dict:
        """Convert VariableInfo to dictionary."""
        return {
            'name': var.name,
            'line': var.line,
            'scope': var.scope
        }

    @staticmethod
    def _loop_to_dict(loop: LoopInfo) -> Dict:
        """Convert LoopInfo to dictionary."""
        return {
            'type': loop.type,
            'line_start': loop.line_start,
            'line_end': loop.line_end,
            'loop_variable': loop.loop_variable,
            'nesting_level': loop.nesting_level
        }

    @staticmethod
    def _conditional_to_dict(cond: ConditionalInfo) -> Dict:
        """Convert ConditionalInfo to dictionary."""
        return {
            'type': cond.type,
            'line': cond.line,
            'has_elif': cond.has_elif,
            'has_else': cond.has_else
        }

    @staticmethod
    def _call_to_dict(call: FunctionCallInfo) -> Dict:
        """Convert FunctionCallInfo to dictionary."""
        return {
            'function': call.function,
            'line': call.line,
            'arguments_count': call.arguments_count
        }


# Convenience function for quick analysis
def analyze_code(source_code: str) -> Dict[str, Any]:
    """
    Quick function to analyze code.

    Args:
        source_code: Python source code as a string

    Returns:
        Dictionary containing extracted code facts
    """
    analyzer = StaticAnalyzer()
    return analyzer.analyze(source_code)
