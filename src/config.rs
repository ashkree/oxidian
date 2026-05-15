use core::panic;
use std::fs;
use std::io::ErrorKind;

use serde::Deserialize;

#[derive(Deserialize, Debug)]
pub struct Config {
    pub vault: VaultConfig,
    pub parse: ParserConfig,
    pub embed: EmbeddingConfig,
    pub db: DatabaseConfig,
}

#[derive(Deserialize, Debug)]
pub struct VaultConfig {
    pub path: String,
    pub directory_blacklist: Vec<String>,
}

#[derive(Deserialize, Debug)]
struct ParserConfig {
    frontmatter_blacklist: Vec<String>,
}

#[derive(Deserialize, Debug)]
struct EmbeddingConfig {
    provider: String,
    model: String,
    batch_size: i32,
}

#[derive(Deserialize, Debug)]
struct DatabaseConfig {
    db_path: String,
    embedding_size: i32,
}

impl Config {
    pub fn load_config(config_file: impl AsRef<std::path::Path>) -> Config {
        let config_contents =
            fs::read_to_string(config_file).unwrap_or_else(|error| match error.kind() {
                ErrorKind::NotFound => panic!("File not found: {error}"),
                _ => panic!("Error while opening file: {error}"),
            });

        match toml::from_str(&config_contents) {
            Ok(conf) => conf,
            Err(error) => panic!("Error while parsing file: {error}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture(name: &str) -> std::path::PathBuf {
        std::path::Path::new("tests/fixtures").join(name)
    }

    #[test]
    fn test_valid_config_loads() {
        let config = Config::load_config(fixture("valid_config.toml"));
        assert_eq!(config.vault.path, "tests/fixtures/sample_vault");
        assert_eq!(config.embed.batch_size, 32);
        assert_eq!(config.db.embedding_size, 1536);
    }

    #[test]
    #[should_panic(expected = "File not found")]
    fn test_missing_file_panics() {
        Config::load_config("nonexistent.toml");
    }

    #[test]
    #[should_panic(expected = "Error while parsing file")]
    fn test_missing_section_panics() {
        Config::load_config(fixture("missing_section.toml"));
    }

    #[test]
    #[should_panic(expected = "Error while parsing file")]
    fn test_wrong_type_panics() {
        Config::load_config(fixture("wrong_type.toml"));
    }
}
