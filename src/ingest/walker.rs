use std::{
    fs,
    path::{Path, PathBuf},
    time::SystemTime,
};

use crate::config::Config;

#[derive(Debug)]
pub struct VaultFile {
    pub path: String,
    pub mtime: SystemTime,
}

pub fn walk_vault(conf: Config) -> Vec<VaultFile> {
    let vault_path = PathBuf::from(&conf.vault.path);

    match vault_path.try_exists() {
        Ok(true) => {}
        Ok(false) => panic!("Path does not exist: {}", vault_path.display()),
        Err(error) => panic!("Error accessing path: {error}"),
    }

    walk_dir(vault_path)
}

fn walk_dir(path: impl AsRef<Path>) -> Vec<VaultFile> {
    let mut vault_files: Vec<VaultFile> = Vec::new();

    let contents = match fs::read_dir(path) {
        Ok(rd) => rd,
        Err(_) => return vault_files,
    };

    for entry in contents {
        let entry = match entry {
            Ok(e) => e,
            Err(_) => continue,
        };

        let file_type = match entry.file_type() {
            Ok(ft) => ft,
            Err(_) => continue,
        };

        if file_type.is_dir() {
            vault_files.extend(walk_dir(entry.path()));
        } else {
            let metadata = match entry.metadata() {
                Ok(m) => m,
                Err(_) => continue,
            };
            let modified = match metadata.modified() {
                Ok(mtime) => mtime,
                Err(_) => continue,
            };
            vault_files.push(VaultFile {
                path: entry.path().to_string_lossy().to_string(),
                mtime: modified,
            });
        }
    }

    vault_files
}
