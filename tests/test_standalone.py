from standalone_app.main import build_parser


def test_standalone_parser_builds():
    parser = build_parser()
    assert parser.prog == "geomorphx-standalone"