#pragma once

#include "printguard/pdf/canonical_model.hpp"
#include <qpdf/QPDF.hh>
#include <string>
#include <vector>

namespace printguard::pdf {

class PdfLoader {
public:
    static DocumentModel load_from_file(const std::string& filepath);
    static DocumentModel load_from_memory(const std::vector<char>& data);

private:
    static double points_to_mm(double points);
    static DocumentModel extract_from_qpdf(QPDF& pdf);
};

} // namespace printguard::pdf
