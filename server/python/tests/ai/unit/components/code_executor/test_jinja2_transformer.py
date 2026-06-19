"""
Jinja2 模板转换器测试

验证 Jinja2 模板转换器的功能。

测试覆盖：
- 转换器创建
- 默认模板
- 响应格式化
- 运行器脚本
- 预加载脚本
"""


from ai.components.code_executor import Jinja2TemplateTransformer, TemplateTransformer


class TestJinja2TemplateTransformerBasics:
    """Jinja2TemplateTransformer 基础测试"""

    def test_transformer_exists(self):
        """测试转换器存在"""
        assert Jinja2TemplateTransformer is not None
        assert isinstance(Jinja2TemplateTransformer, type)

    def test_inherits_from_template_transformer(self):
        """测试继承自 TemplateTransformer"""
        assert issubclass(Jinja2TemplateTransformer, TemplateTransformer)

    def test_has_transform_response_method(self):
        """测试有 transform_response 方法"""
        assert hasattr(Jinja2TemplateTransformer, "transform_response")
        assert callable(Jinja2TemplateTransformer.transform_response)

    def test_has_get_runner_script_method(self):
        """测试有 get_runner_script 方法"""
        assert hasattr(Jinja2TemplateTransformer, "get_runner_script")
        assert callable(Jinja2TemplateTransformer.get_runner_script)

    def test_has_get_preload_script_method(self):
        """测试有 get_preload_script 方法"""
        assert hasattr(Jinja2TemplateTransformer, "get_preload_script")
        assert callable(Jinja2TemplateTransformer.get_preload_script)


class TestJinja2TemplateTransformerMethods:
    """Jinja2TemplateTransformer 方法测试"""

    def test_transform_response_with_result(self):
        """测试转换包含结果的响应"""
        # 响应格式：<<r>>result<<r>>
        response = "<<r>>Hello World<<r>>"
        result = Jinja2TemplateTransformer.transform_response(response)

        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"] == "Hello World"

    def test_transform_response_with_empty_result(self):
        """测试转换空结果响应"""
        response = "<<r>><<r>>"
        result = Jinja2TemplateTransformer.transform_response(response)

        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"] == ""

    def test_get_runner_script_returns_string(self):
        """测试 get_runner_script 返回字符串"""
        script = Jinja2TemplateTransformer.get_runner_script()

        assert isinstance(script, str)
        assert len(script) > 0

    def test_get_runner_script_contains_code_placeholder(self):
        """测试 get_runner_script 包含代码占位符"""
        script = Jinja2TemplateTransformer.get_runner_script()

        # 脚本应该包含代码占位符
        assert Jinja2TemplateTransformer._code_placeholder in script

    def test_get_runner_script_contains_inputs_placeholder(self):
        """测试 get_runner_script 包含输入占位符"""
        script = Jinja2TemplateTransformer.get_runner_script()

        # 脚本应该包含输入占位符
        assert Jinja2TemplateTransformer._inputs_placeholder in script

    def test_get_runner_script_contains_jinja2_import(self):
        """测试 get_runner_script 包含 jinja2 导入"""
        script = Jinja2TemplateTransformer.get_runner_script()

        # 脚本应该导入 jinja2
        assert "import jinja2" in script

    def test_get_runner_script_contains_main_function(self):
        """测试 get_runner_script 包含 main 函数"""
        script = Jinja2TemplateTransformer.get_runner_script()

        # 脚本应该定义 main 函数
        assert "def main" in script

    def test_get_preload_script_returns_string(self):
        """测试 get_preload_script 返回字符串"""
        script = Jinja2TemplateTransformer.get_preload_script()

        assert isinstance(script, str)
        assert len(script) > 0

    def test_get_preload_script_contains_jinja2_import(self):
        """测试 get_preload_script 包含 jinja2 导入"""
        script = Jinja2TemplateTransformer.get_preload_script()

        # 脚本应该导入 jinja2
        assert "import jinja2" in script

    def test_get_preload_script_contains_preload_function(self):
        """测试 get_preload_script 包含预加载函数"""
        script = Jinja2TemplateTransformer.get_preload_script()

        # 脚本应该定义预加载函数
        assert "_jinja2_preload_" in script


class TestJinja2TemplateTransformerTemplate:
    """Jinja2TemplateTransformer 模板测试"""

    def test_template_rendering_logic(self):
        """测试模板渲染逻辑"""
        # 验证运行器脚本中的模板渲染逻辑
        script = Jinja2TemplateTransformer.get_runner_script()

        # 脚本应该包含模板渲染代码
        assert "jinja2.Template" in script
        assert "template.render" in script

    def test_runner_script_structure(self):
        """测试运行器脚本结构"""
        script = Jinja2TemplateTransformer.get_runner_script()

        # 验证脚本结构
        # 1. 定义 main 函数
        assert "def main(**inputs):" in script
        # 2. 导入 json
        assert "import json" in script
        # 3. 解码输入
        assert "b64decode" in script
        # 4. 执行主函数
        assert "main(**inputs_obj)" in script
        # 5. 输出结果
        assert "<<r>>" in script


class TestJinja2TemplateTransformerPlaceholders:
    """Jinja2TemplateTransformer 占位符测试"""

    def test_code_placeholder_exists(self):
        """测试代码占位符存在"""
        assert hasattr(Jinja2TemplateTransformer, "_code_placeholder")
        assert isinstance(Jinja2TemplateTransformer._code_placeholder, str)

    def test_inputs_placeholder_exists(self):
        """测试输入占位符存在"""
        assert hasattr(Jinja2TemplateTransformer, "_inputs_placeholder")
        assert isinstance(Jinja2TemplateTransformer._inputs_placeholder, str)

    def test_placeholders_are_unique(self):
        """测试占位符唯一"""
        code_placeholder = Jinja2TemplateTransformer._code_placeholder
        inputs_placeholder = Jinja2TemplateTransformer._inputs_placeholder

        assert code_placeholder != inputs_placeholder


class TestJinja2TemplateTransformerResponseFormat:
    """Jinja2TemplateTransformer 响应格式测试"""

    def test_extract_result_simple(self):
        """测试提取简单结果"""
        response = "<<r>>Hello<<r>>"
        result = Jinja2TemplateTransformer.transform_response(response)

        assert result["result"] == "Hello"

    def test_extract_result_with_special_chars(self):
        """测试提取包含特殊字符的结果"""
        response = "<<r>>Hello, World! @#$%^&*()<<r>>"
        result = Jinja2TemplateTransformer.transform_response(response)

        assert result["result"] == "Hello, World! @#$%^&*()"

    def test_extract_result_multiline(self):
        """测试提取多行结果"""
        response = "<<r>>Line1\nLine2\nLine3<<r>>"
        result = Jinja2TemplateTransformer.transform_response(response)

        assert result["result"] == "Line1\nLine2\nLine3"
