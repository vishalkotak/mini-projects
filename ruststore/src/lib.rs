use sha2::{Sha256, Digest};
use std::fs;
use std::io;
use std::path::PathBuf;

pub struct StorageEngine {
    base_path: PathBuf,
}

impl StorageEngine {
    pub fn new(base_path: PathBuf) -> Result<Self, io::Error> {
        fs::create_dir_all(&base_path)?;
        Ok(StorageEngine { base_path })
    }

    pub fn put(&self, data: &[u8]) -> Result<String, io::Error> {
        let mut hasher = Sha256::new();
        hasher.update(data);
        let hash = hex::encode(hasher.finalize());
        let file_path = self.base_path.join(&hash);
        fs::write(&file_path, data)?;
        Ok(hash)
    }

    pub fn get(&self, id: &str) -> Result<Vec<u8>, io::Error> {
        let file_path = self.base_path.join(id);
        fs::read(&file_path)
    }

    pub fn delete(&self, id: &str) -> Result<(), io::Error> {
        let file_path = self.base_path.join(id);
        fs::remove_file(&file_path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::Path;
    
    fn setup() -> StorageEngine {
        let path = PathBuf::from("/tmp/ruststore-test");
        StorageEngine::new(path).unwrap()
    }

    #[test]
    fn test_put_and_get() {
        let engine = setup();
        let data = b"hello ruststore";
        let id = engine.put(data).unwrap();
        let retrieved = engine.get(&id).unwrap();
        assert_eq!(data.to_vec(), retrieved);
    }

    #[test]
    fn test_put_returns_consistent_hash() {
        let engine = setup();
        let data = b"some content";
        let id1 = engine.put(data).unwrap();
        let id2 = engine.put(data).unwrap();
        assert_eq!(id1, id2);
    }

    #[test]
    fn test_delete() {
        let engine = setup();
        let data = b"delete me";
        let id = engine.put(data).unwrap();
        engine.delete(&id).unwrap();
        assert!(engine.get(&id).is_err());
    }

    #[test]
    fn test_get_noexistent() {
        let engine = setup();
        let result = engine.get("nonexistent");
        assert!(result.is_err());
    }
}
