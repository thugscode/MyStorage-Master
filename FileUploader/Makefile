# Makefile for High-Performance File Zipper

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O3 -march=native -DNDEBUG -flto -fomit-frame-pointer
PERF_FLAGS = -std=c++20 -Wall -Wextra -O3 -march=native -DNDEBUG -flto -fomit-frame-pointer -funroll-loops -finline-functions
DEBUG_FLAGS = -std=c++17 -Wall -Wextra -O0 -g -fsanitize=address
TARGET = high_performance_zipper
SOURCE = high_performance_zipper.cpp
LIBS = -lzip -pthread

# Default target - build high-performance version
all: $(TARGET)

# Compile the high-performance version
$(TARGET): $(SOURCE)
	$(CXX) $(PERF_FLAGS) -o $(TARGET) $(SOURCE) $(LIBS)

# High-performance target with maximum optimizations
performance: $(TARGET)

# Debug version
debug: $(SOURCE)
	$(CXX) $(DEBUG_FLAGS) -o $(TARGET)_debug $(SOURCE) $(LIBS)

# Profile version with profiling information
profile: $(SOURCE)
	$(CXX) -std=c++20 -Wall -Wextra -O2 -pg -g -o $(TARGET)_profile $(SOURCE) $(LIBS)

# Clean build files
clean:
	rm -f $(TARGET) $(TARGET)_debug $(TARGET)_profile

# Clean build files and output folder
clean-all:
	rm -f $(TARGET) $(TARGET)_debug $(TARGET)_profile
	rm -rf output/

# Install dependencies (Ubuntu/Debian)
install-deps:
	sudo apt-get update
	sudo apt-get install -y libzip-dev build-essential

# Install dependencies (CentOS/RHEL/Fedora)
install-deps-fedora:
	sudo dnf install -y libzip-devel gcc-c++ make

# Run the high-performance file zipper
run: $(TARGET)
	./$(TARGET)

# Run the GUI version
gui:
	python3 high_performance_gui_zipper.py

# Run the one-click script
one-click:
	./run_zipper.sh

# Benchmark comparison
benchmark: $(TARGET)
	@echo "=== Performance Benchmark ==="
	@echo "High-performance version:"
	@time ./$(TARGET) > /dev/null 2>&1 || true

# Comprehensive performance test
performance-test: $(TARGET)
	@echo "Running comprehensive performance test..."
	./performance_test.sh

# Memory usage analysis
memory-check: $(TARGET)_debug
	valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all ./$(TARGET)_debug

# CPU profiling
cpu-profile: $(TARGET)_profile
	./$(TARGET)_profile
	gprof $(TARGET)_profile gmon.out > profile_report.txt
	@echo "Profile report generated in profile_report.txt"

# Static analysis
static-analysis: $(SOURCE)
	cppcheck --enable=all --std=c++20 $(SOURCE) || echo "Install cppcheck for static analysis"

# Generate assembly for optimization analysis
assembly: $(SOURCE)
	$(CXX) $(PERF_FLAGS) -S -o $(TARGET).s $(SOURCE)

# Help
help:
	@echo "Available targets:"
	@echo "  all           - Build the high-performance file zipper program"
	@echo "  $(TARGET)     - Build the high-performance file zipper"
	@echo "  performance   - Build high-performance version with max optimizations"
	@echo "  debug         - Build debug version with sanitizers"
	@echo "  profile       - Build profiling version"
	@echo "  clean         - Remove build files"
	@echo "  clean-all     - Remove build files and output folder"
	@echo "  install-deps  - Install dependencies (Ubuntu/Debian)"
	@echo "  install-deps-fedora - Install dependencies (Fedora/CentOS/RHEL)"
	@echo "  run           - Build and run the high-performance file zipper"
	@echo "  gui           - Run the high-performance GUI version"
	@echo "  one-click     - Run the one-click script"
	@echo "  benchmark     - Performance benchmark"
	@echo "  performance-test - Run comprehensive performance test suite"
	@echo "  memory-check  - Run memory analysis with valgrind"
	@echo "  cpu-profile   - Generate CPU profiling report"
	@echo "  static-analysis - Run static code analysis"
	@echo "  assembly      - Generate assembly code for optimization analysis"
	@echo "  help          - Show this help message"

.PHONY: all performance clean clean-all install-deps install-deps-fedora run gui one-click benchmark performance-test debug profile memory-check cpu-profile static-analysis assembly help
