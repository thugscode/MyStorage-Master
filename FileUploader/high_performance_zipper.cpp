#include <iostream>
#include <string>
#include <string_view>
#include <filesystem>
#include <vector>
#include <memory>
#include <zip.h>
#include <chrono>
#include <thread>
#include <future>
#include <algorithm>
#include <execution>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <array>
#include <unordered_set>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <fstream>
#include <memory_resource>

namespace fs = std::filesystem;

// MIME type utility class
class MimeTypeMapper {
private:
    static const std::unordered_map<std::string, std::string> mimeTypes;
    
public:
    static std::string getMimeType(const std::string& extension) {
        // Convert extension to lowercase for lookup
        std::string lowerExt = extension;
        std::transform(lowerExt.begin(), lowerExt.end(), lowerExt.begin(), ::tolower);
        
        // Remove leading dot if present
        if (!lowerExt.empty() && lowerExt[0] == '.') {
            lowerExt = lowerExt.substr(1);
        }
        
        auto it = mimeTypes.find(lowerExt);
        return (it != mimeTypes.end()) ? it->second : "application/octet-stream";
    }
    
    static std::string getFileExtension(const std::string& filename) {
        const auto lastDot = filename.find_last_of('.');
        if (lastDot != std::string::npos && lastDot < filename.length() - 1) {
            return filename.substr(lastDot + 1);
        }
        return "";
    }
};

// Define the MIME type mapping
const std::unordered_map<std::string, std::string> MimeTypeMapper::mimeTypes = {
    {"pdf", "application/pdf"},
    {"docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    {"xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    {"pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    {"doc", "application/msword"},
    {"xls", "application/vnd.ms-excel"},
    {"ppt", "application/vnd.ms-powerpoint"},
    {"jpg", "image/jpeg"},
    {"jpeg", "image/jpeg"},
    {"png", "image/png"},
    {"gif", "image/gif"},
    {"svg", "image/svg+xml"},
    {"zip", "application/zip"},
    {"txt", "text/plain"}
};

// File metadata for JSON output
struct FileMetadata {
    std::string name;
    std::string type;
    
    FileMetadata(const std::string& zipName, const std::string& originalFilename) 
        : name(zipName) {
        const std::string extension = MimeTypeMapper::getFileExtension(originalFilename);
        type = MimeTypeMapper::getMimeType(extension);
    }
};

// Memory pool for better allocation performance
class MemoryPool {
private:
    std::pmr::unsynchronized_pool_resource pool;
    
public:
    MemoryPool() : pool(std::pmr::get_default_resource()) {}
    
    std::pmr::memory_resource* get_resource() {
        return &pool;
    }
};

// Thread-safe statistics with atomic operations
class ThreadSafeStats {
private:
    std::atomic<size_t> totalFiles{0};
    std::atomic<size_t> processedFiles{0};
    std::atomic<size_t> skippedFiles{0};
    std::atomic<size_t> failedFiles{0};
    std::atomic<size_t> totalInputSize{0};
    std::atomic<size_t> totalOutputSize{0};
    std::chrono::time_point<std::chrono::high_resolution_clock> startTime;
    
public:
    void setStartTime() { startTime = std::chrono::high_resolution_clock::now(); }
    void incrementTotalFiles() { totalFiles.fetch_add(1, std::memory_order_relaxed); }
    void incrementProcessedFiles() { processedFiles.fetch_add(1, std::memory_order_relaxed); }
    void incrementSkippedFiles() { skippedFiles.fetch_add(1, std::memory_order_relaxed); }
    void incrementFailedFiles() { failedFiles.fetch_add(1, std::memory_order_relaxed); }
    void addInputSize(size_t size) { totalInputSize.fetch_add(size, std::memory_order_relaxed); }
    void addOutputSize(size_t size) { totalOutputSize.fetch_add(size, std::memory_order_relaxed); }
    
    void displayResults() const {
        const auto endTime = std::chrono::high_resolution_clock::now();
        const auto processingTime = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime);
        
        std::cout << "\n=== Processing Summary ===\n";
        std::cout << "Files processed: " << processedFiles.load() << '\n';
        std::cout << "Files skipped: " << skippedFiles.load() << '\n';
        std::cout << "Files failed: " << failedFiles.load() << '\n';
        std::cout << "Total files: " << totalFiles.load() << '\n';
        
        const auto procFiles = processedFiles.load();
        if (procFiles > 0) {
            std::cout << "\n=== Compression Statistics ===\n";
            const auto inputSize = totalInputSize.load();
            const auto outputSize = totalOutputSize.load();
            
            std::cout << "Total input size: " << formatBytes(inputSize) << '\n';
            std::cout << "Total output size: " << formatBytes(outputSize) << '\n';
            
            if (inputSize > 0) {
                const auto overallCompression = (1.0 - static_cast<double>(outputSize) / inputSize) * 100.0;
                std::cout << "Overall compression: " << std::fixed << std::setprecision(1) << overallCompression << "%\n";
            }
            
            std::cout << "Processing time: " << processingTime.count() << " ms\n";
            
            if (processingTime.count() > 0) {
                const auto throughput = static_cast<double>(inputSize) / (processingTime.count() / 1000.0);
                std::cout << "Throughput: " << formatBytes(static_cast<size_t>(throughput)) << "/s\n";
            }
        }
    }
    
    bool hasFailures() const { return failedFiles.load() > 0; }
    
private:
    static std::string formatBytes(size_t bytes) {
        constexpr std::array<const char*, 6> units = {"B", "KB", "MB", "GB", "TB", "PB"};
        
        if (bytes == 0) return "0 B";
        
        const auto unitIndex = std::min(
            static_cast<size_t>(std::log2(static_cast<double>(bytes)) / 10.0),
            static_cast<size_t>(units.size() - 1)
        );
        
        const auto value = static_cast<double>(bytes) / std::pow(1024.0, static_cast<double>(unitIndex));
        
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(1) << value << " " << units[unitIndex];
        return oss.str();
    }
};

// Configuration with better defaults and validation
class Config {
public:
    static constexpr std::string_view DEFAULT_INPUT_FOLDER = "input";
    static constexpr std::string_view DEFAULT_OUTPUT_FOLDER = "output";
    // No default password - must be provided via environment variable
    static constexpr size_t MAX_THREADS = 8;  // Reasonable default
    static constexpr size_t MIN_FILE_SIZE_FOR_THREADING = 1024 * 1024;  // 1MB
    
    // Get configuration value with fallback to default
    static std::string getInputFolder() {
        const char* env = std::getenv("ZIPPER_INPUT_FOLDER");
        return env ? std::string(env) : std::string(DEFAULT_INPUT_FOLDER);
    }
    
    static std::string getOutputFolder() {
        const char* env = std::getenv("ZIPPER_OUTPUT_FOLDER");
        return env ? std::string(env) : std::string(DEFAULT_OUTPUT_FOLDER);
    }
    
    static std::string getPassword() {
        const char* env = std::getenv("ZIPPER_PASSWORD");
        if (!env || std::string(env).empty()) {
            throw std::runtime_error("Password not provided! Please set ZIPPER_PASSWORD environment variable.");
        }
        return std::string(env);
    }
    static constexpr size_t BUFFER_SIZE = 64 * 1024;  // 64KB buffer
    
    static void displayHeader() {
        std::cout << "=== High-Performance File Zipper with Password Protection ===\n";
        std::cout << "Source folder: " << getInputFolder() << '\n';
        std::cout << "Output folder: " << getOutputFolder() << '\n';
        std::cout << "Encryption: AES-256\n";
        std::cout << "Max threads: " << getOptimalThreadCount() << '\n';
        std::cout << "Password: [USER PROVIDED]\n\n";
    }
    
    static size_t getOptimalThreadCount() {
        const auto hw_threads = std::thread::hardware_concurrency();
        return std::min(static_cast<size_t>(hw_threads > 0 ? hw_threads : 4), MAX_THREADS);
    }
};

// RAII wrapper for zip archives with better error handling
class ZipArchive {
private:
    zip_t* archive = nullptr;
    fs::path filePath;
    
public:
    explicit ZipArchive(const fs::path& path) : filePath(path) {
        int error = 0;
        archive = zip_open(path.c_str(), ZIP_CREATE | ZIP_TRUNCATE, &error);
        if (!archive) {
            std::string errorMsg = "Failed to create zip archive: " + path.string();
            if (error != 0) {
                zip_error_t zipError;
                zip_error_init_with_code(&zipError, error);
                errorMsg += " (Error: " + std::string(zip_error_strerror(&zipError)) + ")";
                zip_error_fini(&zipError);
            }
            throw std::runtime_error(errorMsg);
        }
    }
    
    ~ZipArchive() {
        if (archive) {
            if (zip_close(archive) < 0) {
                std::cerr << "Warning: Failed to properly close zip archive: " << filePath << '\n';
            }
        }
    }
    
    zip_t* get() const { return archive; }
    
    // Non-copyable, moveable
    ZipArchive(const ZipArchive&) = delete;
    ZipArchive& operator=(const ZipArchive&) = delete;
    ZipArchive(ZipArchive&& other) noexcept : archive(other.archive), filePath(std::move(other.filePath)) {
        other.archive = nullptr;
    }
    ZipArchive& operator=(ZipArchive&& other) noexcept {
        if (this != &other) {
            if (archive) zip_close(archive);
            archive = other.archive;
            filePath = std::move(other.filePath);
            other.archive = nullptr;
        }
        return *this;
    }
};

// File processing task for better parallelization
struct FileTask {
    fs::path inputFile;
    fs::path outputFile;
    size_t fileSize;
    
    FileTask(fs::path input, fs::path output, size_t size)
        : inputFile(std::move(input)), outputFile(std::move(output)), fileSize(size) {}
};

class HighPerformanceFileZipper {
private:
    const fs::path inputFolder;
    const fs::path outputFolder;
    const std::string password;
    mutable ThreadSafeStats stats;
    MemoryPool memPool;
    
    // Cache for file modification times to avoid repeated filesystem calls
    mutable std::unordered_map<std::string, fs::file_time_type> timeCache;
    mutable std::mutex timeCacheMutex;
    
    // Track processed files for JSON output
    mutable std::vector<FileMetadata> processedFiles;
    mutable std::mutex processedFilesMutex;

public:
    explicit HighPerformanceFileZipper(std::string_view inputDir, std::string_view outputDir, std::string_view pwd)
        : inputFolder(inputDir), outputFolder(outputDir), password(pwd) {}

    bool processAllFiles() noexcept {
        try {
            stats.setStartTime();
            
            // Early validation
            if (!validateDirectories()) return false;
            
            // Get files to process with pre-filtering and sizing
            auto filesToProcess = getFilesToProcess();
            if (filesToProcess.empty()) {
                std::cout << "No new files to process.\n";
                return true;
            }

            std::cout << "Found " << filesToProcess.size() << " files to process\n";
            
            // Sort by file size (largest first) for better load balancing
            std::sort(filesToProcess.begin(), filesToProcess.end(),
                [](const FileTask& a, const FileTask& b) {
                    return a.fileSize > b.fileSize;
                });
            
            // Determine processing strategy based on file sizes and count
            const bool useParallel = shouldUseParallelProcessing(filesToProcess);
            
            if (useParallel) {
                std::cout << "Using parallel processing with " << Config::getOptimalThreadCount() << " threads\n";
                processFilesParallel(filesToProcess);
            } else {
                std::cout << "Using sequential processing\n";
                processFilesSequential(filesToProcess);
            }
            
            // Display comprehensive results
            stats.displayResults();
            
            // Generate files-list.json
            generateFileListJson();
            
            return !stats.hasFailures();

        } catch (const std::exception& e) {
            std::cerr << "Critical error: " << e.what() << '\n';
            return false;
        }
    }

private:
    bool validateDirectories() const {
        // Create output directory if needed
        if (!fs::exists(outputFolder)) {
            try {
                fs::create_directories(outputFolder);
                std::cout << "Created output folder: " << outputFolder << '\n';
            } catch (const fs::filesystem_error& e) {
                std::cerr << "Failed to create output folder: " << e.what() << '\n';
                return false;
            }
        }

        // Validate input folder
        if (!fs::exists(inputFolder)) {
            std::cerr << "Input folder does not exist: " << inputFolder << '\n';
            return false;
        }

        if (!fs::is_directory(inputFolder)) {
            std::cerr << "Input path is not a directory: " << inputFolder << '\n';
            return false;
        }

        return true;
    }
    
    std::vector<FileTask> getFilesToProcess() const {
        std::vector<FileTask> filesToProcess;
        filesToProcess.reserve(100);
        
        try {
            // Pre-build cache of existing zip files for faster lookup
            std::unordered_set<std::string> existingZips;
            if (fs::exists(outputFolder)) {
                for (const auto& entry : fs::directory_iterator(outputFolder)) {
                    if (entry.is_regular_file() && entry.path().extension() == ".zip") {
                        existingZips.insert(entry.path().filename().string());
                    }
                }
            }
            
            // Scan input directory
            for (const auto& entry : fs::directory_iterator(inputFolder)) {
                if (!entry.is_regular_file()) continue;
                
                const auto& inputFile = entry.path();
                const auto zipFileName = getZipFileName(inputFile.filename().string());
                const auto zipFile = outputFolder / zipFileName;
                
                // Quick check using our cache
                const bool zipExists = existingZips.find(zipFileName) != existingZips.end();
                
                // Only add if output doesn't exist or is older
                if (!zipExists || isInputNewer(inputFile, zipFile)) {
                    const auto fileSize = fs::file_size(inputFile);
                    filesToProcess.emplace_back(inputFile, zipFile, fileSize);
                    stats.incrementTotalFiles();
                }
            }
        } catch (const fs::filesystem_error& e) {
            std::cerr << "Error scanning input directory: " << e.what() << '\n';
        }
        
        return filesToProcess;
    }
    
    bool shouldUseParallelProcessing(const std::vector<FileTask>& tasks) const {
        if (tasks.size() < 2) return false;
        
        // Use parallel processing if we have multiple files and at least one large file
        const size_t largeFiles = std::count_if(tasks.begin(), tasks.end(),
            [](const FileTask& task) { return task.fileSize >= Config::MIN_FILE_SIZE_FOR_THREADING; });
        
        return largeFiles > 0 || tasks.size() >= Config::getOptimalThreadCount();
    }
    
    void processFilesSequential(const std::vector<FileTask>& tasks) const {
        for (size_t i = 0; i < tasks.size(); ++i) {
            if (tasks.size() > 1) {
                std::cout << "[" << (i + 1) << "/" << tasks.size() << "] ";
            }
            processFileTask(tasks[i]);
        }
    }
    
    void processFilesParallel(const std::vector<FileTask>& tasks) const {
        const size_t numThreads = std::min(Config::getOptimalThreadCount(), tasks.size());
        std::vector<std::future<void>> futures;
        futures.reserve(numThreads);
        
        std::atomic<size_t> taskIndex{0};
        std::mutex progressMutex;
        
        for (size_t i = 0; i < numThreads; ++i) {
            futures.emplace_back(std::async(std::launch::async, [&]() {
                while (true) {
                    const size_t currentIndex = taskIndex.fetch_add(1, std::memory_order_relaxed);
                    if (currentIndex >= tasks.size()) break;
                    
                    {
                        std::lock_guard<std::mutex> lock(progressMutex);
                        if (tasks.size() > 1) {
                            std::cout << "[" << (currentIndex + 1) << "/" << tasks.size() << "] ";
                        }
                    }
                    
                    processFileTask(tasks[currentIndex]);
                }
            }));
        }
        
        // Wait for all threads to complete
        for (auto& future : futures) {
            future.wait();
        }
    }
    
    void processFileTask(const FileTask& task) const {
        const auto fileName = task.inputFile.filename().string();
        const auto zipFileName = task.outputFile.filename().string();

        try {
            stats.addInputSize(task.fileSize);

            if (createPasswordProtectedZip(task.inputFile, task.outputFile)) {
                const auto outputSize = fs::file_size(task.outputFile);
                stats.addOutputSize(outputSize);
                stats.incrementProcessedFiles();
                
                // Add to processed files list for JSON output
                {
                    std::lock_guard<std::mutex> lock(processedFilesMutex);
                    processedFiles.emplace_back(zipFileName, fileName);
                }
                
                const auto compressionRatio = (1.0 - static_cast<double>(outputSize) / task.fileSize) * 100.0;
                
                // Thread-safe output
                {
                    static std::mutex outputMutex;
                    std::lock_guard<std::mutex> lock(outputMutex);
                    std::cout << "✅ " << zipFileName << " (" << formatBytes(task.fileSize) 
                              << " → " << formatBytes(outputSize) 
                              << ", " << std::fixed << std::setprecision(1) << compressionRatio << "% compressed)\n";
                }
            } else {
                stats.incrementFailedFiles();
                {
                    static std::mutex outputMutex;
                    std::lock_guard<std::mutex> lock(outputMutex);
                    std::cerr << "❌ Failed: " << fileName << '\n';
                }
            }
        } catch (const fs::filesystem_error& e) {
            stats.incrementFailedFiles();
            {
                static std::mutex outputMutex;
                std::lock_guard<std::mutex> lock(outputMutex);
                std::cerr << "❌ File error for " << fileName << ": " << e.what() << '\n';
            }
        }
    }

    bool createPasswordProtectedZip(const fs::path& inputFile, const fs::path& outputZipPath) const {
        try {
            ZipArchive archive(outputZipPath);
            return addFileToZipOptimized(archive.get(), inputFile);
        } catch (const std::exception& e) {
            std::cerr << "Zip creation error: " << e.what() << '\n';
            // Clean up failed zip file
            std::error_code ec;
            fs::remove(outputZipPath, ec);
            return false;
        }
    }

    bool addFileToZipOptimized(zip_t* archive, const fs::path& filePath) const {
        // For small files, use zip_source_file. For large files, use buffered approach
        const auto fileSize = fs::file_size(filePath);
        
        if (fileSize <= Config::MIN_FILE_SIZE_FOR_THREADING) {
            return addFileToZipSimple(archive, filePath);
        } else {
            return addFileToZipBuffered(archive, filePath);
        }
    }
    
    bool addFileToZipSimple(zip_t* archive, const fs::path& filePath) const {
        // Create zip source from file
        zip_source_t* source = zip_source_file(archive, filePath.c_str(), 0, 0);
        if (!source) {
            std::cerr << "Failed to create zip source for: " << filePath << '\n';
            return false;
        }

        // Add file with just filename (not full path)
        const auto fileName = filePath.filename().string();
        const zip_int64_t index = zip_file_add(archive, fileName.c_str(), source, ZIP_FL_OVERWRITE);
        
        if (index < 0) {
            zip_source_free(source);
            std::cerr << "Failed to add file to zip: " << fileName << '\n';
            return false;
        }

        // Set AES-256 encryption with compression
        if (zip_file_set_encryption(archive, index, ZIP_EM_AES_256, password.c_str()) < 0) {
            std::cerr << "Failed to set encryption for: " << fileName << '\n';
            return false;
        }
        
        // Set compression method (deflate with best compression)
        if (zip_set_file_compression(archive, index, ZIP_CM_DEFLATE, 9) < 0) {
            std::cerr << "Warning: Failed to set compression for: " << fileName << '\n';
            // Continue anyway - encryption is more important
        }

        return true;
    }
    
    bool addFileToZipBuffered(zip_t* archive, const fs::path& filePath) const {
        // For large files, we could implement a custom source callback
        // For now, fall back to simple method as libzip handles buffering internally
        return addFileToZipSimple(archive, filePath);
    }

    static std::string getZipFileName(const std::string& fileName) {
        // Keep the original filename with extension and add .zip
        // This creates format: filename.ext.zip instead of filename.zip
        return fileName + ".zip";
    }

    bool isInputNewer(const fs::path& inputFile, const fs::path& zipFile) const {
        try {
            // Use cache for repeated lookups
            std::lock_guard<std::mutex> lock(timeCacheMutex);
            
            const auto inputKey = inputFile.string();
            auto inputTime = timeCache.find(inputKey);
            if (inputTime == timeCache.end()) {
                inputTime = timeCache.emplace(inputKey, fs::last_write_time(inputFile)).first;
            }
            
            const auto zipKey = zipFile.string();
            auto zipTime = timeCache.find(zipKey);
            if (zipTime == timeCache.end()) {
                if (!fs::exists(zipFile)) return true;
                zipTime = timeCache.emplace(zipKey, fs::last_write_time(zipFile)).first;
            }
            
            return inputTime->second > zipTime->second;
        } catch (const fs::filesystem_error&) {
            return true; // If we can't compare, assume input is newer
        }
    }
    
    void generateFileListJson() const {
        try {
            std::lock_guard<std::mutex> lock(processedFilesMutex);
            
            if (processedFiles.empty()) {
                std::cout << "No files processed, skipping JSON generation.\n";
                return;
            }
            
            const fs::path jsonPath = outputFolder / "files-list.json";
            std::ofstream jsonFile(jsonPath);
            
            if (!jsonFile.is_open()) {
                std::cerr << "Failed to create files-list.json\n";
                return;
            }
            
            jsonFile << "[\n";
            
            for (size_t i = 0; i < processedFiles.size(); ++i) {
                const auto& file = processedFiles[i];
                jsonFile << "    {\n";
                jsonFile << "        \"name\": \"" << escapeJsonString(file.name) << "\",\n";
                jsonFile << "        \"type\": \"" << escapeJsonString(file.type) << "\"\n";
                jsonFile << "    }";
                
                if (i < processedFiles.size() - 1) {
                    jsonFile << ",";
                }
                jsonFile << "\n";
            }
            
            jsonFile << "]\n";
            jsonFile.close();
            
            std::cout << "📄 Generated files-list.json with " << processedFiles.size() << " entries\n";
            
        } catch (const std::exception& e) {
            std::cerr << "Error generating files-list.json: " << e.what() << '\n';
        }
    }
    
    static std::string escapeJsonString(const std::string& str) {
        std::string escaped;
        escaped.reserve(str.size() + 16); // Reserve some extra space for escapes
        
        for (char c : str) {
            switch (c) {
                case '"':  escaped += "\\\""; break;
                case '\\': escaped += "\\\\"; break;
                case '\b': escaped += "\\b"; break;
                case '\f': escaped += "\\f"; break;
                case '\n': escaped += "\\n"; break;
                case '\r': escaped += "\\r"; break;
                case '\t': escaped += "\\t"; break;
                default:
                    if (c < 0x20) {
                        // Control characters
                        escaped += "\\u";
                        char buf[5];
                        std::snprintf(buf, sizeof(buf), "%04x", static_cast<unsigned char>(c));
                        escaped += buf;
                    } else {
                        escaped += c;
                    }
                    break;
            }
        }
        
        return escaped;
    }

    static std::string formatBytes(size_t bytes) {
        constexpr std::array<const char*, 6> units = {"B", "KB", "MB", "GB", "TB", "PB"};
        
        if (bytes == 0) return "0 B";
        
        const auto unitIndex = std::min(
            static_cast<size_t>(std::log2(static_cast<double>(bytes)) / 10.0),
            static_cast<size_t>(units.size() - 1)
        );
        
        const auto value = static_cast<double>(bytes) / std::pow(1024.0, static_cast<double>(unitIndex));
        
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(1) << value << " " << units[unitIndex];
        return oss.str();
    }
};

int main() {
    Config::displayHeader();
    
    try {
        const auto inputFolder = Config::getInputFolder();
        const auto outputFolder = Config::getOutputFolder();
        const auto password = Config::getPassword();
        
        HighPerformanceFileZipper zipper(inputFolder, outputFolder, password);
        
        std::cout << "Source folder: " << inputFolder << "\n";
        std::cout << "Output folder: " << outputFolder << "\n";
        std::cout << "Scanning files...\n";
        const bool success = zipper.processAllFiles();

        if (success) {
            std::cout << "\n🎉 Process completed successfully!\n";
            std::cout << "Check the '" << outputFolder << "' folder for individual zip files.\n";
            std::cout << "Each zip file is protected with AES-256 encryption.\n";
        } else {
            std::cout << "\n❌ Process completed with errors!\n";
            return 1;
        }

    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << '\n';
        return 1;
    }

    return 0;
}
