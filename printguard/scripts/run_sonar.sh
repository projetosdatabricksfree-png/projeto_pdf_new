#!/bin/bash

# Script to run SonarQube analysis using Docker
# Usage: ./run_sonar.sh <SONAR_TOKEN>

TOKEN=$1

if [ -z "$TOKEN" ]; then
    echo "Error: SonarQube token is required."
    echo "Usage: $0 <SONAR_TOKEN>"
    exit 1
fi

# Get the absolute path of the project root (where sonar-project.properties is)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting coverage and SonarQube analysis for project at $PROJECT_DIR..."

# 1. Build and Run Tests with Coverage
echo "Step 1: Building and running tests with coverage..."
cmake -B "$PROJECT_DIR/build" -S "$PROJECT_DIR" -DCMAKE_BUILD_TYPE=Debug -DPRINTGUARD_COVERAGE=ON
cmake --build "$PROJECT_DIR/build" --target unit_tests
cd "$PROJECT_DIR/build" && ctest --output-on-failure
cd "$PROJECT_DIR"

# 2. Generate Coverage XML using gcovr
echo "Step 2: Generating coverage XML..."
gcovr -r . --sonarqube build/coverage.xml

# 3. Trigger SonarScanner
echo "Step 3: Triggering SonarScanner..."
docker run --rm \
    --network="host" \
    --user 0:0 \
    -e SONAR_HOST_URL="http://localhost:9000" \
    -e SONAR_SCANNER_OPTS="-Dsonar.login=$TOKEN" \
    -v "$PROJECT_DIR:/usr/src" \
    -v /usr/include:/usr/include:ro \
    -v /usr/lib/gcc:/usr/lib/gcc:ro \
    -v /usr/local/include:/usr/local/include:ro \
    sonarsource/sonar-scanner-cli -X

echo "Analysis triggered. Check the results at http://localhost:9000"
