"""Jinja2 模板转换器"""

from textwrap import dedent

from ai.components.code_executor.template_transformer import TemplateTransformer


class Jinja2TemplateTransformer(TemplateTransformer):
    """Jinja2 模板转换器"""

    @classmethod
    def transform_response(cls, response: str) -> dict:
        """
        转换响应为字典

        Args:
            response: 响应

        Returns:
            dict: 转换后的字典
        """

        return {"result": cls.extract_result_str_from_response(response)}

    @classmethod
    def get_runner_script(cls) -> str:
        """获取运行器脚本"""
        runner_script = dedent(f"""
            # declare main function
            def main(**inputs):
                import jinja2
                template = jinja2.Template('''{cls._code_placeholder}''')
                return template.render(**inputs)

            import json
            from base64 import b64decode

            # decode and prepare input dict
            inputs_obj = json.loads(b64decode('{cls._inputs_placeholder}').decode('utf-8'))

            # execute main function
            output = main(**inputs_obj)

            # convert output and print
            result = f'''<<r>>{{output}}<<r>>'''
            print(result)

            """)
        return runner_script

    @classmethod
    def get_preload_script(cls) -> str:
        """获取预加载脚本"""
        preload_script = dedent("""
            import jinja2
            from base64 import b64decode

            def _jinja2_preload_():
                # prepare jinja2 environment, load template and render before to avoid sandbox issue
                template = jinja2.Template('{{s}}')
                template.render(s='a')

            if __name__ == '__main__':
                _jinja2_preload_()

            """)

        return preload_script
