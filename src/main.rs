use crate::{config::Config, ingest::walker};

mod config;
mod ingest;

fn main() {
    let conf = Config::load_config("./tests/fixtures/valid_config.toml");

    let vault_files = walker::walk_vault(conf);

    for file in vault_files {
        println!("{:#?}", file);
    }
}
