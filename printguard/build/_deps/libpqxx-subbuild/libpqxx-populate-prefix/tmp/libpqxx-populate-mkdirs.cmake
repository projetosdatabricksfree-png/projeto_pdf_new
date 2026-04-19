# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-src"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-build"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-subbuild/libpqxx-populate-prefix"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-subbuild/libpqxx-populate-prefix/tmp"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-subbuild/libpqxx-populate-prefix/src/libpqxx-populate-stamp"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-subbuild/libpqxx-populate-prefix/src"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-subbuild/libpqxx-populate-prefix/src/libpqxx-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-subbuild/libpqxx-populate-prefix/src/libpqxx-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build/_deps/libpqxx-subbuild/libpqxx-populate-prefix/src/libpqxx-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
