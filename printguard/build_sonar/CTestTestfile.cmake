# CMake generated Testfile for 
# Source directory: /home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard
# Build directory: /home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
subdirs("_deps/spdlog-build")
subdirs("_deps/httplib-build")
subdirs("_deps/catch2-build")
subdirs("_deps/libpqxx-build")
subdirs("src/common")
subdirs("src/persistence")
subdirs("src/storage")
subdirs("src/domain")
subdirs("src/orchestration")
subdirs("src/pdf")
subdirs("src/analysis")
subdirs("src/fix")
subdirs("src/render")
subdirs("src/report")
subdirs("apps/api")
subdirs("apps/worker")
subdirs("apps/inspect")
subdirs("apps/cli")
subdirs("tests")
