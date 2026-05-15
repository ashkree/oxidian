use crate::config::Config;
use std::{path::PathBuf, time::SystemTime};
use walkdir::WalkDir;

#[derive(Debug)]
pub struct VaultFile {
    pub path: String,
    pub mtime: SystemTime,
}

pub fn walk_vault(conf: Config) -> Vec<VaultFile> {
    let vault_path = PathBuf::from(&conf.vault.path);
    let blacklist = &conf.vault.directory_blacklist;

    if !vault_path.exists() {
        panic!("Path does not exist: {}", vault_path.display());
    }

    WalkDir::new(&vault_path)
        .into_iter()
        .filter_entry(|e| {
            // Skip blacklisted dirs
            if e.file_type().is_dir() {
                let relative = e
                    .path()
                    .strip_prefix(&vault_path)
                    .unwrap()
                    .to_string_lossy();
                return !blacklist.contains(&relative.to_string());
            }
            true
        })
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .filter_map(|e| {
            let mtime = e.metadata().ok()?.modified().ok()?;
            Some(VaultFile {
                path: e.path().to_string_lossy().to_string(),
                mtime,
            })
        })
        .collect()
}
