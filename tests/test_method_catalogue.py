from cli.geomorphx_cli import build_parser
from geomorphx.methods import METHODS
from standalone_app.main import build_parser as standalone_parser


def test_original_qgis_method_indices_remain_compatible_with_saved_models():
    assert METHODS[:6] == (
        "rrim_baseline", "rrim_multiscale", "rrim_anisotropic",
        "rrim_anisotropic_multiscale", "rrim_structural", "rrim_plus",
    )


def test_every_catalogue_method_is_available_in_both_command_interfaces():
    for method in METHODS:
        args = build_parser().parse_args([
            "compute", "--dem", "dem.tif", "--out", "out.tif", "--method", method,
        ])
        assert args.method == method
        args = standalone_parser().parse_args([
            "compute-batch", "--dem-dir", "dems", "--out-dir", "out", "--method", method,
        ])
        assert args.method == method
