from aiohttp_apispec import AiohttpApiSpec
from aiohttp import web
from pathlib import Path
from jinja2 import Template


class CustomAiohttpApiSpec(AiohttpApiSpec):
    def _add_swagger_web_page(
        self, app: web.Application, static_path: str, view_path: str
    ):
        static_files = Path(__file__).parent / "static"
        app.router.add_static(static_path, static_files)

        with open(str(static_files / "index.html")) as swg_tmp:
            tmp = Template(swg_tmp.read()).render(
                path=self.url, static=static_path)

        async def swagger_view(_):
            return web.Response(text=tmp, content_type="text/html")

        app.router.add_route(
            "GET", view_path, swagger_view, name="swagger.docs")


def custom_setup_aiohttp_apispec(
    app: web.Application,
    *,
    title: str = "API documentation",
    version: str = "0.0.1",
    url: str = "/api/docs/swagger.json",
    request_data_name: str = "data",
    swagger_path: str = None,
    static_path: str = '/static/swagger',
    error_callback=None,
    in_place: bool = False,
    prefix: str = '',
    **kwargs
) -> None:
    CustomAiohttpApiSpec(
        url,
        app,
        request_data_name,
        title=title,
        version=version,
        swagger_path=swagger_path,
        static_path=static_path,
        error_callback=error_callback,
        in_place=in_place,
        prefix=prefix,
        **kwargs
    )
