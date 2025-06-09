use pyo3::prelude::*;
use std::collections::HashMap;
use sqlx::{SqlitePool, Pool, sqlite::SqlitePoolOptions};
use tokio::runtime::Runtime;

#[pyfunction]
pub fn get_rustypot_data() -> PyResult<Vec<HashMap<String, String>>> {
    let rt = Runtime::new()?;
    
    rt.block_on(async {
        let pool = SqlitePoolOptions::new()
            .connect("sqlite:skins.db")
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to connect to DB: {}", e)))?;

        let items = sqlx::query_as::<_, (String, f64)>("SELECT name, price FROM rustypot_items")
            .fetch_all(&pool)
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("DB query failed: {}", e)))?;

        Ok(items.into_iter().map(|(name, price)| {
            let mut map = HashMap::new();
            map.insert("name".to_string(), name);
            map.insert("deposit_price".to_string(), price.to_string());
            map.insert("withdraw_price".to_string(), price.to_string());
            map.insert("have".to_string(), "1".to_string());
            map.insert("max".to_string(), "100".to_string());
            map
        }).collect())
    })
}

#[pymodule]
fn rustypot_ffi(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_rustypot_data, m)?)?;
    Ok(())
}