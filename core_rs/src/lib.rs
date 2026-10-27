//! GeoMorphX Rust kernels (Phase 3).

use ndarray::ArrayView2;
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2};
use pyo3::prelude::*;
use rayon::prelude::*;

fn validate_grid(dem: &ArrayView2<f32>, window: usize) -> PyResult<()> {
    if dem.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err("DEM cannot be empty"));
    }
    if window < 3 || window % 2 == 0 || window.checked_mul(window).is_none() {
        return Err(pyo3::exceptions::PyValueError::new_err("window must be odd and >= 3"));
    }
    Ok(())
}

fn numpy_gradient(dem_view: &ArrayView2<f32>) -> (ndarray::Array2<f32>, ndarray::Array2<f32>) {
    let rows = dem_view.shape()[0];
    let cols = dem_view.shape()[1];

    let mut gy = ndarray::Array2::<f32>::zeros((rows, cols));
    let mut gx = ndarray::Array2::<f32>::zeros((rows, cols));

    // gy (gradient along axis 0)
    for c in 0..cols {
        if rows > 1 {
            gy[[0, c]] = dem_view[[1, c]] - dem_view[[0, c]];
            for r in 1..(rows - 1) {
                gy[[r, c]] = (dem_view[[r + 1, c]] - dem_view[[r - 1, c]]) / 2.0;
            }
            gy[[rows - 1, c]] = dem_view[[rows - 1, c]] - dem_view[[rows - 2, c]];
        }
    }

    // gx (gradient along axis 1)
    for r in 0..rows {
        if cols > 1 {
            gx[[r, 0]] = dem_view[[r, 1]] - dem_view[[r, 0]];
            for c in 1..(cols - 1) {
                gx[[r, c]] = (dem_view[[r, c + 1]] - dem_view[[r, c - 1]]) / 2.0;
            }
            gx[[r, cols - 1]] = dem_view[[r, cols - 1]] - dem_view[[r, cols - 2]];
        }
    }

    (gy, gx)
}

#[pyfunction]
fn local_relief_rs<'py>(
    py: Python<'py>,
    dem: PyReadonlyArray2<'py, f32>,
    window: usize,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let dem_view = dem.as_array();
    validate_grid(&dem_view, window)?;
    let rows = dem_view.shape()[0];
    let cols = dem_view.shape()[1];
    let radius = (window / 2) as isize;

    let mut out = ndarray::Array2::<f32>::zeros((rows, cols));

    out.outer_iter_mut()
        .into_par_iter()
        .enumerate()
        .for_each(|(r, mut out_row)| {
            let r_isize = r as isize;
            for c in 0..cols {
                let c_isize = c as isize;
                let mut min_val = f32::MAX;
                let mut max_val = f32::MIN;

                for wr in -radius..=radius {
                    let pr = (r_isize + wr).clamp(0, (rows - 1) as isize) as usize;
                    for wc in -radius..=radius {
                        let pc = (c_isize + wc).clamp(0, (cols - 1) as isize) as usize;
                        let val = dem_view[[pr, pc]];
                        if !val.is_finite() {
                            min_val = f32::NAN;
                            max_val = f32::NAN;
                        }
                        if val < min_val {
                            min_val = val;
                        }
                        if val > max_val {
                            max_val = val;
                        }
                    }
                }
                out_row[c] = max_val - min_val;
            }
        });

    Ok(out.into_pyarray_bound(py))
}

#[pyfunction]
fn local_std_rs<'py>(
    py: Python<'py>,
    dem: PyReadonlyArray2<'py, f32>,
    window: usize,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let dem_view = dem.as_array();
    validate_grid(&dem_view, window)?;
    let rows = dem_view.shape()[0];
    let cols = dem_view.shape()[1];
    let radius = (window / 2) as isize;
    let n = (window * window) as f64;

    let mut out = ndarray::Array2::<f32>::zeros((rows, cols));

    out.outer_iter_mut()
        .into_par_iter()
        .enumerate()
        .for_each(|(r, mut out_row)| {
            let r_isize = r as isize;
            for c in 0..cols {
                let c_isize = c as isize;

                let mut sum = 0.0;
                for wr in -radius..=radius {
                    let pr = (r_isize + wr).clamp(0, (rows - 1) as isize) as usize;
                    for wc in -radius..=radius {
                        let pc = (c_isize + wc).clamp(0, (cols - 1) as isize) as usize;
                        sum += dem_view[[pr, pc]] as f64;
                    }
                }
                let mean = sum / n;

                let mut sq_sum = 0.0;
                for wr in -radius..=radius {
                    let pr = (r_isize + wr).clamp(0, (rows - 1) as isize) as usize;
                    for wc in -radius..=radius {
                        let pc = (c_isize + wc).clamp(0, (cols - 1) as isize) as usize;
                        let diff = dem_view[[pr, pc]] as f64 - mean;
                        sq_sum += diff * diff;
                    }
                }
                out_row[c] = (sq_sum / n).sqrt() as f32;
            }
        });

    Ok(out.into_pyarray_bound(py))
}

#[pyfunction]
fn local_mean_rs<'py>(
    py: Python<'py>,
    dem: PyReadonlyArray2<'py, f32>,
    window: usize,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let dem_view = dem.as_array();
    validate_grid(&dem_view, window)?;
    let rows = dem_view.shape()[0];
    let cols = dem_view.shape()[1];
    let radius = (window / 2) as isize;
    let n = (window * window) as f64;

    let mut out = ndarray::Array2::<f32>::zeros((rows, cols));

    out.outer_iter_mut()
        .into_par_iter()
        .enumerate()
        .for_each(|(r, mut out_row)| {
            let r_isize = r as isize;
            for c in 0..cols {
                let c_isize = c as isize;
                let mut sum = 0.0;
                for wr in -radius..=radius {
                    let pr = (r_isize + wr).clamp(0, (rows - 1) as isize) as usize;
                    for wc in -radius..=radius {
                        let pc = (c_isize + wc).clamp(0, (cols - 1) as isize) as usize;
                        sum += dem_view[[pr, pc]] as f64;
                    }
                }
                out_row[c] = (sum / n) as f32;
            }
        });

    Ok(out.into_pyarray_bound(py))
}

#[pyfunction]
fn directional_gradient_response_rs<'py>(
    py: Python<'py>,
    dem: PyReadonlyArray2<'py, f32>,
    azimuth_deg: f32,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let dem_view = dem.as_array();
    validate_grid(&dem_view, 3)?;
    if !azimuth_deg.is_finite() {
        return Err(pyo3::exceptions::PyValueError::new_err("azimuth must be finite"));
    }
    let (gy, gx) = numpy_gradient(&dem_view);

    let theta = (azimuth_deg % 360.0).to_radians();
    let ux = theta.cos();
    let uy = theta.sin();

    let rows = dem_view.shape()[0];
    let cols = dem_view.shape()[1];
    let mut response = ndarray::Array2::<f32>::zeros((rows, cols));

    ndarray::Zip::from(&mut response)
        .and(&gx)
        .and(&gy)
        .par_for_each(|resp, &x, &y| {
            *resp = (x * ux + y * uy).abs();
        });

    Ok(response.into_pyarray_bound(py))
}

#[pymodule]
fn geomorphx_core_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(local_relief_rs, m)?)?;
    m.add_function(wrap_pyfunction!(local_std_rs, m)?)?;
    m.add_function(wrap_pyfunction!(local_mean_rs, m)?)?;
    m.add_function(wrap_pyfunction!(directional_gradient_response_rs, m)?)?;
    Ok(())
}
