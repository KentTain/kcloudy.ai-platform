"""Python3 模板转换器"""

from textwrap import dedent

from ai.components.code_executor.template_transformer import TemplateTransformer


class Python3TemplateTransformer(TemplateTransformer):
    """Python3 模板转换器"""

    @classmethod
    def get_runner_script(cls) -> str:
        """获取运行器脚本"""
        runner_script = dedent(f"""
            # declare main function
            {cls._code_placeholder}

            import json
            from base64 import b64decode

            # decode and prepare input dict
            inputs_obj = json.loads(b64decode('{cls._inputs_placeholder}').decode('utf-8'))

            # execute main function
            output_obj = main(**inputs_obj)

            # convert output to json and print
            output_json = json.dumps(output_obj, indent=4)
            result = f'''<<r>>{{output_json}}<<r>>'''
            print(result)
            """)
        return runner_script
