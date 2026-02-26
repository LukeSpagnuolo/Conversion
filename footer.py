import dash_bootstrap_components as dbc
from dash import html


class Footer():

    def __init__(self, logo_src=None, medal_src=None):
        self.logo_src = logo_src or "/assets/img/csi-pacific-logo-reverse.png"
        self.medal_src = medal_src or "/assets/img/csi-medal.png"

    def render(self, id="footer"):
        """
        Dash footer component styled with a black background, white text,
        and fixed to the bottom of the viewport.
        """
        return html.Footer(

            [
                # Copyright text

                dbc.Container([

                    html.P(
                        "© 2025 CSI Pacific",
                        className="col-md-4 mb-0"
                    ),

                    # Logo or brand link
                    html.A(
                        html.Img(
                            src=self.logo_src,
                            height="60px",
                        ),
                        href="/builder",
                        className=(
                            "col-md-4 d-flex align-items-center justify-content-center mb-3"
                            " mb-md-0 me-md-auto text-decoration-none"
                        ),
                        **{"aria-label": "CSI Pacific"}
                    ),

                    # Navigation links
                    html.Ul(
                        [
                            html.Li(
                                html.A(
                                    html.Img(
                                        src=self.medal_src,
                                        height="42px",
                                    ),
                                    href="/builder",
                                    className="text-decoration-none"
                                ),
                                className="nav-item"
                            ),
                        ],
                        className="nav col-md-4 justify-content-end"
                    ),
                ],
                    className="d-flex flex-wrap justify-content-between align-items-center py-3  "
                )],
            className="mt-4 text-white border-top border-light fixed-bottom",
            id=id,
            style={"backgroundColor": "#000000"}
        )
