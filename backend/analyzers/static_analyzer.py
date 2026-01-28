"""
Static Code Analyzer

Analyzes Python source code without executing it.
Extracts structural information using AST (Abstract Syntax Tree).

Enhanced to support:
- Class definitions and methods
- Decorators
- List/dict/set comprehensions
- Generator expressions
- Exception handling (try/except/finally)
- Import statements
- Type annotations
- Nested functions/closures
- Async functions and await expressions
- Context managers (with statements)
"""

import ast
from typing import Dict, List, Any, Set, Optional, Tuple
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
    # Enhanced fields
    is_async: bool = False
    is_method: bool = False
    is_generator: bool = False
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    return_type: Optional[str] = None
    param_types: Dict[str, str] = field(default_factory=dict)
    has_yield: bool = False
    nested_functions: List[str] = field(default_factory=list)
    complexity: int = 1  # Cyclomatic complexity estimate


@dataclass
class ClassInfo:
    """Information about a class definition."""

    name: str
    line_start: int
    line_end: int
    bases: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    class_variables: List[str] = field(default_factory=list)
    instance_variables: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    has_init: bool = False
    is_dataclass: bool = False


@dataclass
class VariableInfo:
    """Information about a variable."""

    name: str
    line: int
    scope: str  # 'global', class name, or function name
    # Enhanced fields
    type_annotation: Optional[str] = None
    is_constant: bool = False  # UPPER_CASE convention
    is_class_var: bool = False
    is_instance_var: bool = False


@dataclass
class LoopInfo:
    """Information about a loop."""

    type: str  # 'for' or 'while'
    line_start: int
    line_end: int
    loop_variable: Optional[str] = None  # For 'for' loops
    nesting_level: int = 0
    # Enhanced fields
    iterable_type: Optional[str] = None  # 'range', 'list', 'dict', etc.
    is_comprehension: bool = False
    has_break: bool = False
    has_continue: bool = False
    has_else: bool = False


@dataclass
class ConditionalInfo:
    """Information about an if statement."""

    type: str  # 'if'
    line: int
    has_elif: bool = False
    has_else: bool = False
    # Enhanced fields
    elif_count: int = 0
    is_ternary: bool = False


@dataclass
class FunctionCallInfo:
    """Information about a function call."""

    function: str
    line: int
    arguments_count: int
    # Enhanced fields
    keyword_arguments: List[str] = field(default_factory=list)
    is_method_call: bool = False
    object_name: Optional[str] = None  # For method calls: obj.method()


@dataclass
class ExceptionHandlerInfo:
    """Information about exception handling."""

    line_start: int
    line_end: int
    exception_types: List[str] = field(default_factory=list)
    has_except: bool = True
    has_finally: bool = False
    has_else: bool = False
    is_bare_except: bool = False  # except: without exception type


@dataclass
class ImportInfo:
    """Information about imports."""

    module: str
    line: int
    is_from_import: bool = False
    imported_names: List[str] = field(default_factory=list)
    alias: Optional[str] = None


@dataclass
class ComprehensionInfo:
    """Information about list/dict/set comprehensions and generator expressions."""

    type: str  # 'list', 'dict', 'set', 'generator'
    line: int
    loop_variable: Optional[str] = None
    has_condition: bool = False
    nested_count: int = 1  # Number of for clauses


@dataclass
class ContextManagerInfo:
    """Information about with statements."""

    line: int
    context_expr: str
    variable: Optional[str] = None
    is_async: bool = False


class CodeVisitor(ast.NodeVisitor):
    """
    Custom AST visitor to extract code facts.
    Walks through the AST and collects information about code structures.

    Enhanced to support classes, comprehensions, exception handling, imports,
    decorators, async code, and more.
    """

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.functions: List[FunctionInfo] = []
        self.variables: List[VariableInfo] = []
        self.loops: List[LoopInfo] = []
        self.conditionals: List[ConditionalInfo] = []
        self.function_calls: List[FunctionCallInfo] = []

        # Enhanced collections
        self.classes: List[ClassInfo] = []
        self.exception_handlers: List[ExceptionHandlerInfo] = []
        self.imports: List[ImportInfo] = []
        self.comprehensions: List[ComprehensionInfo] = []
        self.context_managers: List[ContextManagerInfo] = []

        # Tracking context
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
        self.loop_depth: int = 0
        self.function_names: Set[str] = set()
        self.class_names: Set[str] = set()

    def _get_decorator_names(self, decorator_list: List) -> List[str]:
        """Extract decorator names from a list of decorator nodes."""
        names = []
        for decorator in decorator_list:
            if isinstance(decorator, ast.Name):
                names.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                names.append(f"{self._get_full_attr_name(decorator)}")
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    names.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    names.append(self._get_full_attr_name(decorator.func))
        return names

    def _get_full_attr_name(self, node: ast.Attribute) -> str:
        """Get full attribute name like 'module.submodule.attr'."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))

    def _get_type_annotation(self, annotation) -> Optional[str]:
        """Extract type annotation as string."""
        if annotation is None:
            return None
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            # Handle generics like List[int], Dict[str, int]
            if isinstance(annotation.value, ast.Name):
                base = annotation.value.id
                if isinstance(annotation.slice, ast.Tuple):
                    args = ', '.join(self._get_type_annotation(el) or '?' for el in annotation.slice.elts)
                else:
                    args = self._get_type_annotation(annotation.slice) or '?'
                return f"{base}[{args}]"
        elif isinstance(annotation, ast.Attribute):
            return self._get_full_attr_name(annotation)
        return ast.unparse(annotation) if hasattr(ast, 'unparse') else str(annotation)

    def _get_docstring(self, node) -> Optional[str]:
        """Extract docstring from function/class body."""
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                return node.body[0].value.value
        return None

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity estimate."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                complexity += len(child.generators)
        return complexity

    def _get_iterable_type(self, node) -> Optional[str]:
        """Determine the type of iterable in a for loop."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id  # range, enumerate, zip, etc.
        elif isinstance(node, ast.Name):
            return 'variable'
        elif isinstance(node, ast.List):
            return 'list_literal'
        elif isinstance(node, ast.Tuple):
            return 'tuple_literal'
        elif isinstance(node, ast.Dict):
            return 'dict_literal'
        elif isinstance(node, ast.Set):
            return 'set_literal'
        elif isinstance(node, ast.Str) or (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            return 'string'
        elif isinstance(node, ast.Attribute):
            return 'attribute'
        return None

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit a class definition."""
        self.class_names.add(node.name)

        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(self._get_full_attr_name(base))

        # Create class info
        class_info = ClassInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
            bases=bases,
            decorators=self._get_decorator_names(node.decorator_list),
            docstring=self._get_docstring(node),
        )

        # Check for dataclass decorator
        class_info.is_dataclass = 'dataclass' in class_info.decorators

        # Set current class context
        prev_class = self.current_class
        self.current_class = node.name

        # Analyze class body
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                class_info.methods.append(item.name)
                if item.name == '__init__':
                    class_info.has_init = True
                    # Extract instance variables from __init__
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute):
                                    if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                        class_info.instance_variables.append(target.attr)
            elif isinstance(item, ast.Assign):
                # Class-level variables
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info.class_variables.append(target.id)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                class_info.class_variables.append(item.target.id)

        self.classes.append(class_info)

        # Continue visiting children
        self.generic_visit(node)

        # Restore previous class context
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit a function definition."""
        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit an async function definition."""
        self._visit_function(node, is_async=True)

    def _visit_function(self, node, is_async: bool = False):
        """Common handler for function and async function definitions."""
        # Store function name for later reference
        self.function_names.add(node.name)

        # Extract parameters with type annotations
        params = [arg.arg for arg in node.args.args]
        param_types = {}
        for arg in node.args.args:
            if arg.annotation:
                param_types[arg.arg] = self._get_type_annotation(arg.annotation)

        # Create function info
        func_info = FunctionInfo(
            name=node.name,
            params=params,
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
            is_async=is_async,
            is_method=self.current_class is not None,
            decorators=self._get_decorator_names(node.decorator_list),
            docstring=self._get_docstring(node),
            return_type=self._get_type_annotation(node.returns),
            param_types=param_types,
            complexity=self._calculate_complexity(node),
        )

        # Set current function context
        prev_function = self.current_function
        self.current_function = node.name

        # Check for recursion, conditionals, loops, returns, yields, nested functions
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

            elif isinstance(child, (ast.Yield, ast.YieldFrom)):
                func_info.has_yield = True
                func_info.is_generator = True

            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child is not node:  # Don't count the function itself
                    func_info.nested_functions.append(child.name)

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
        if self.current_class and not self.current_function:
            scope = self.current_class
        elif self.current_function:
            scope = self.current_function
        else:
            scope = "global"

        for target in node.targets:
            if isinstance(target, ast.Name):
                is_constant = target.id.isupper() and '_' in target.id or target.id.isupper()
                var_info = VariableInfo(
                    name=target.id,
                    line=node.lineno,
                    scope=scope,
                    is_constant=is_constant,
                    is_class_var=self.current_class is not None and self.current_function is None,
                )
                self.variables.append(var_info)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit an annotated assignment (e.g., x: int = 5)."""
        if self.current_class and not self.current_function:
            scope = self.current_class
        elif self.current_function:
            scope = self.current_function
        else:
            scope = "global"

        if isinstance(node.target, ast.Name):
            var_info = VariableInfo(
                name=node.target.id,
                line=node.lineno,
                scope=scope,
                type_annotation=self._get_type_annotation(node.annotation),
                is_class_var=self.current_class is not None and self.current_function is None,
            )
            self.variables.append(var_info)

        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        """Visit a for loop."""
        loop_var = None
        if isinstance(node.target, ast.Name):
            loop_var = node.target.id
        elif isinstance(node.target, ast.Tuple):
            loop_var = ', '.join(
                elt.id for elt in node.target.elts if isinstance(elt, ast.Name)
            )

        # Check for break/continue in the loop body
        has_break = any(isinstance(child, ast.Break) for child in ast.walk(node))
        has_continue = any(isinstance(child, ast.Continue) for child in ast.walk(node))

        loop_info = LoopInfo(
            type="for",
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
            loop_variable=loop_var,
            nesting_level=self.loop_depth,
            iterable_type=self._get_iterable_type(node.iter),
            has_break=has_break,
            has_continue=has_continue,
            has_else=len(node.orelse) > 0,
        )
        self.loops.append(loop_info)

        # Increase loop depth for nested loops
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node: ast.While):
        """Visit a while loop."""
        # Check for break/continue in the loop body
        has_break = any(isinstance(child, ast.Break) for child in ast.walk(node))
        has_continue = any(isinstance(child, ast.Continue) for child in ast.walk(node))

        loop_info = LoopInfo(
            type="while",
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
            nesting_level=self.loop_depth,
            has_break=has_break,
            has_continue=has_continue,
            has_else=len(node.orelse) > 0,
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
        elif_count = 0

        # Count elif branches
        current = node
        while current.orelse:
            if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                has_elif = True
                elif_count += 1
                current = current.orelse[0]
            else:
                has_else = True
                break

        cond_info = ConditionalInfo(
            type="if",
            line=node.lineno,
            has_elif=has_elif,
            has_else=has_else,
            elif_count=elif_count,
        )
        self.conditionals.append(cond_info)

        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp):
        """Visit a ternary/conditional expression (a if condition else b)."""
        cond_info = ConditionalInfo(
            type="if",
            line=node.lineno,
            is_ternary=True,
        )
        self.conditionals.append(cond_info)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Visit a function call."""
        func_name = None
        is_method_call = False
        object_name = None

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            is_method_call = True
            if isinstance(node.func.value, ast.Name):
                object_name = node.func.value.id

        # Extract keyword argument names
        keyword_args = [kw.arg for kw in node.keywords if kw.arg is not None]

        if func_name:
            call_info = FunctionCallInfo(
                function=func_name,
                line=node.lineno,
                arguments_count=len(node.args),
                keyword_arguments=keyword_args,
                is_method_call=is_method_call,
                object_name=object_name,
            )
            self.function_calls.append(call_info)

        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        """Visit a try/except/finally block."""
        exception_types = []
        is_bare_except = False

        for handler in node.handlers:
            if handler.type is None:
                is_bare_except = True
            elif isinstance(handler.type, ast.Name):
                exception_types.append(handler.type.id)
            elif isinstance(handler.type, ast.Tuple):
                for exc in handler.type.elts:
                    if isinstance(exc, ast.Name):
                        exception_types.append(exc.id)

        handler_info = ExceptionHandlerInfo(
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
            exception_types=exception_types,
            has_except=len(node.handlers) > 0,
            has_finally=len(node.finalbody) > 0,
            has_else=len(node.orelse) > 0,
            is_bare_except=is_bare_except,
        )
        self.exception_handlers.append(handler_info)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Visit an import statement."""
        for alias in node.names:
            import_info = ImportInfo(
                module=alias.name,
                line=node.lineno,
                is_from_import=False,
                alias=alias.asname,
            )
            self.imports.append(import_info)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit a from ... import statement."""
        imported_names = [alias.name for alias in node.names]
        import_info = ImportInfo(
            module=node.module or '',
            line=node.lineno,
            is_from_import=True,
            imported_names=imported_names,
        )
        self.imports.append(import_info)

    def visit_ListComp(self, node: ast.ListComp):
        """Visit a list comprehension."""
        self._visit_comprehension(node, 'list')
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        """Visit a set comprehension."""
        self._visit_comprehension(node, 'set')
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp):
        """Visit a dict comprehension."""
        self._visit_comprehension(node, 'dict')
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        """Visit a generator expression."""
        self._visit_comprehension(node, 'generator')
        self.generic_visit(node)

    def _visit_comprehension(self, node, comp_type: str):
        """Common handler for comprehensions."""
        generators = node.generators
        loop_var = None
        if generators and isinstance(generators[0].target, ast.Name):
            loop_var = generators[0].target.id

        has_condition = any(len(gen.ifs) > 0 for gen in generators)

        comp_info = ComprehensionInfo(
            type=comp_type,
            line=node.lineno,
            loop_variable=loop_var,
            has_condition=has_condition,
            nested_count=len(generators),
        )
        self.comprehensions.append(comp_info)

    def visit_With(self, node: ast.With):
        """Visit a with statement (context manager)."""
        for item in node.items:
            context_expr = ast.unparse(item.context_expr) if hasattr(ast, 'unparse') else str(item.context_expr)
            variable = None
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                variable = item.optional_vars.id

            cm_info = ContextManagerInfo(
                line=node.lineno,
                context_expr=context_expr,
                variable=variable,
                is_async=False,
            )
            self.context_managers.append(cm_info)

        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        """Visit an async with statement."""
        for item in node.items:
            context_expr = ast.unparse(item.context_expr) if hasattr(ast, 'unparse') else str(item.context_expr)
            variable = None
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                variable = item.optional_vars.id

            cm_info = ContextManagerInfo(
                line=node.lineno,
                context_expr=context_expr,
                variable=variable,
                is_async=True,
            )
            self.context_managers.append(cm_info)

        self.generic_visit(node)


class StaticAnalyzer:
    """
    Main static analyzer class.
    Analyzes Python source code and extracts structural information.

    Enhanced to provide comprehensive analysis of complex Python code including
    classes, comprehensions, exception handling, imports, and more.
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
            source_lines = source_code.split("\n")

            # Create visitor and walk the tree
            visitor = CodeVisitor(source_lines)
            visitor.visit(tree)

            # Calculate aggregate complexity
            total_complexity = sum(f.complexity for f in visitor.functions) or 1

            # Compile results with enhanced data
            results = {
                "functions": [self._function_to_dict(f) for f in visitor.functions],
                "variables": [self._variable_to_dict(v) for v in visitor.variables],
                "loops": [self._loop_to_dict(loop) for loop in visitor.loops],
                "conditionals": [
                    self._conditional_to_dict(c) for c in visitor.conditionals
                ],
                "function_calls": [
                    self._call_to_dict(c) for c in visitor.function_calls
                ],
                # New enhanced data
                "classes": [self._class_to_dict(c) for c in visitor.classes],
                "exception_handlers": [
                    self._exception_to_dict(e) for e in visitor.exception_handlers
                ],
                "imports": [self._import_to_dict(i) for i in visitor.imports],
                "comprehensions": [
                    self._comprehension_to_dict(c) for c in visitor.comprehensions
                ],
                "context_managers": [
                    self._context_manager_to_dict(cm) for cm in visitor.context_managers
                ],
                "summary": {
                    "total_functions": len(visitor.functions),
                    "total_variables": len(visitor.variables),
                    "total_loops": len(visitor.loops),
                    "total_conditionals": len(visitor.conditionals),
                    "has_recursion": any(f.is_recursive for f in visitor.functions),
                    "total_lines": len(source_lines),
                    # Enhanced summary data
                    "total_classes": len(visitor.classes),
                    "total_methods": sum(len(c.methods) for c in visitor.classes),
                    "total_exception_handlers": len(visitor.exception_handlers),
                    "total_imports": len(visitor.imports),
                    "total_comprehensions": len(visitor.comprehensions),
                    "total_context_managers": len(visitor.context_managers),
                    "has_async": any(f.is_async for f in visitor.functions),
                    "has_generators": any(f.is_generator for f in visitor.functions),
                    "has_classes": len(visitor.classes) > 0,
                    "has_decorators": any(f.decorators for f in visitor.functions) or any(c.decorators for c in visitor.classes),
                    "total_complexity": total_complexity,
                    "average_complexity": total_complexity / max(len(visitor.functions), 1),
                },
            }

            return results

        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in code: {e}")

    @staticmethod
    def _function_to_dict(func: FunctionInfo) -> Dict:
        """Convert FunctionInfo to dictionary."""
        return {
            "name": func.name,
            "params": func.params,
            "param_count": len(func.params),
            "line_start": func.line_start,
            "line_end": func.line_end,
            "is_recursive": func.is_recursive,
            "has_conditionals": func.has_conditionals,
            "has_loops": func.has_loops,
            "return_count": func.return_count,
            "calls_functions": func.calls_functions,
            # Enhanced fields
            "is_async": func.is_async,
            "is_method": func.is_method,
            "is_generator": func.is_generator,
            "decorators": func.decorators,
            "docstring": func.docstring,
            "return_type": func.return_type,
            "param_types": func.param_types,
            "has_yield": func.has_yield,
            "nested_functions": func.nested_functions,
            "complexity": func.complexity,
        }

    @staticmethod
    def _class_to_dict(cls: ClassInfo) -> Dict:
        """Convert ClassInfo to dictionary."""
        return {
            "name": cls.name,
            "line_start": cls.line_start,
            "line_end": cls.line_end,
            "bases": cls.bases,
            "methods": cls.methods,
            "class_variables": cls.class_variables,
            "instance_variables": cls.instance_variables,
            "decorators": cls.decorators,
            "docstring": cls.docstring,
            "has_init": cls.has_init,
            "is_dataclass": cls.is_dataclass,
            "method_count": len(cls.methods),
        }

    @staticmethod
    def _variable_to_dict(var: VariableInfo) -> Dict:
        """Convert VariableInfo to dictionary."""
        return {
            "name": var.name,
            "line": var.line,
            "scope": var.scope,
            "type_annotation": var.type_annotation,
            "is_constant": var.is_constant,
            "is_class_var": var.is_class_var,
            "is_instance_var": var.is_instance_var,
        }

    @staticmethod
    def _loop_to_dict(loop: LoopInfo) -> Dict:
        """Convert LoopInfo to dictionary."""
        return {
            "type": loop.type,
            "line_start": loop.line_start,
            "line_end": loop.line_end,
            "loop_variable": loop.loop_variable,
            "nesting_level": loop.nesting_level,
            "iterable_type": loop.iterable_type,
            "is_comprehension": loop.is_comprehension,
            "has_break": loop.has_break,
            "has_continue": loop.has_continue,
            "has_else": loop.has_else,
        }

    @staticmethod
    def _conditional_to_dict(cond: ConditionalInfo) -> Dict:
        """Convert ConditionalInfo to dictionary."""
        return {
            "type": cond.type,
            "line": cond.line,
            "has_elif": cond.has_elif,
            "has_else": cond.has_else,
            "elif_count": cond.elif_count,
            "is_ternary": cond.is_ternary,
        }

    @staticmethod
    def _call_to_dict(call: FunctionCallInfo) -> Dict:
        """Convert FunctionCallInfo to dictionary."""
        return {
            "function": call.function,
            "line": call.line,
            "arguments_count": call.arguments_count,
            "keyword_arguments": call.keyword_arguments,
            "is_method_call": call.is_method_call,
            "object_name": call.object_name,
        }

    @staticmethod
    def _exception_to_dict(exc: ExceptionHandlerInfo) -> Dict:
        """Convert ExceptionHandlerInfo to dictionary."""
        return {
            "line_start": exc.line_start,
            "line_end": exc.line_end,
            "exception_types": exc.exception_types,
            "has_except": exc.has_except,
            "has_finally": exc.has_finally,
            "has_else": exc.has_else,
            "is_bare_except": exc.is_bare_except,
        }

    @staticmethod
    def _import_to_dict(imp: ImportInfo) -> Dict:
        """Convert ImportInfo to dictionary."""
        return {
            "module": imp.module,
            "line": imp.line,
            "is_from_import": imp.is_from_import,
            "imported_names": imp.imported_names,
            "alias": imp.alias,
        }

    @staticmethod
    def _comprehension_to_dict(comp: ComprehensionInfo) -> Dict:
        """Convert ComprehensionInfo to dictionary."""
        return {
            "type": comp.type,
            "line": comp.line,
            "loop_variable": comp.loop_variable,
            "has_condition": comp.has_condition,
            "nested_count": comp.nested_count,
        }

    @staticmethod
    def _context_manager_to_dict(cm: ContextManagerInfo) -> Dict:
        """Convert ContextManagerInfo to dictionary."""
        return {
            "line": cm.line,
            "context_expr": cm.context_expr,
            "variable": cm.variable,
            "is_async": cm.is_async,
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
