"""JavaScript 模板转换器"""

from textwrap import dedent

from ai.components.code_executor.template_transformer import TemplateTransformer


class NodeJsTemplateTransformer(TemplateTransformer):
    """NodeJS 模板转换器"""

    @classmethod
    def get_runner_script(cls) -> str:
        """获取运行器脚本"""
        runner_script = dedent(
            f"""
            // declare main function
            {cls._code_placeholder}

            // decode and prepare input object
            var inputs_obj = JSON.parse(Buffer.from('{cls._inputs_placeholder}', 'base64').toString('utf-8'))

            // 智能检测main函数的参数签名并调用
            var output_obj;
            var mainFuncStr = main.toString();

            // 检查是否使用解构参数（包含大括号）
            if (mainFuncStr.match(/\\(\\s*\\{{[^}}]*\\}}\\s*\\)/)) {{
                // 使用解构参数调用
                output_obj = main(inputs_obj);
            }} else {{
                // 使用独立参数调用
                var values = Object.values(inputs_obj);
                output_obj = main.apply(null, values);
            }}

            // convert output to json and print
            var output_json = JSON.stringify(output_obj)
            var result = `<<r>>${{output_json}}<<r>>`
            console.log(result)
            """,
        )
        return runner_script
