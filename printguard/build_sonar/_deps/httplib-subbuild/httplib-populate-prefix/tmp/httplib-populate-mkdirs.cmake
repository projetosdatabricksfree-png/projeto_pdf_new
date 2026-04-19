# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-src"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-build"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-subbuild/httplib-populate-prefix"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-subbuild/httplib-populate-prefix/tmp"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-subbuild/httplib-populate-prefix/src/httplib-populate-stamp"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-subbuild/httplib-populate-prefix/src"
  "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-subbuild/httplib-populate-prefix/src/httplib-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-subbuild/httplib-populate-prefix/src/httplib-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/diego/Desktop/PROJETOS/Projeto_grafica_New/printguard/build_sonar/_deps/httplib-subbuild/httplib-populate-prefix/src/httplib-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
