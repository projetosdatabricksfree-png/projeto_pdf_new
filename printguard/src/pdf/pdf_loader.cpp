#include "printguard/pdf/pdf_loader.hpp"
#include "printguard/common/logging.hpp"
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <cmath>

namespace printguard::pdf {

double PdfLoader::points_to_mm(double points) {
    return points * (25.4 / 72.0);
}

namespace {

double local_points_to_mm(double points) {
    return points * (25.4 / 72.0);
}

}

static Rect qpdf_rect_to_pg_rect(QPDFObjectHandle box) {
    if (!box.isArray() || box.getArrayNItems() != 4) {
        return {0, 0, 0, 0};
    }
    double x1 = box.getArrayItem(0).getNumericValue();
    double y1 = box.getArrayItem(1).getNumericValue();
    double x2 = box.getArrayItem(2).getNumericValue();
    double y2 = box.getArrayItem(3).getNumericValue();
    
    // Normalizing to x, y, w, h
    double x = (x1 < x2) ? x1 : x2;
    double y = (y1 < y2) ? y1 : y2;
    double w = std::abs(x2 - x1);
    double h = std::abs(y2 - y1);
    
    return {
        local_points_to_mm(x),
        local_points_to_mm(y),
        local_points_to_mm(w),
        local_points_to_mm(h)
    };
}

DocumentModel PdfLoader::load_from_file(const std::string& filepath) {
    try {
        QPDF pdf;
        pdf.processFile(filepath.c_str());
        return extract_from_qpdf(pdf);
    } catch (const std::exception& e) {
        PG_LOG_ERROR("QPDF failure loading {}: {}", filepath, e.what());
        throw;
    }
}

DocumentModel PdfLoader::load_from_memory(const std::vector<char>& data) {
    try {
        QPDF pdf;
        pdf.processMemoryFile("input.pdf", data.data(), data.size());
        return extract_from_qpdf(pdf);
    } catch (const std::exception& e) {
        PG_LOG_ERROR("QPDF failure loading from memory: {}", e.what());
        throw;
    }
}

DocumentModel PdfLoader::extract_from_qpdf(QPDF& pdf) {
    DocumentModel model;
    QPDFPageDocumentHelper dh(pdf);
    std::vector<QPDFPageObjectHelper> pages = dh.getAllPages();
    
    model.page_count = static_cast<int>(pages.size());
    model.metadata.is_linearized = pdf.isLinearized();
    model.metadata.is_encrypted = pdf.isEncrypted();
    model.metadata.pdf_version = pdf.getPDFVersion();
    
    // Extract /Info with UTF-8 normalization
    QPDFObjectHandle info = pdf.getTrailer().getKey("/Info");
    if (info.isDictionary()) {
        auto get_string = [&](const std::string& key) {
            QPDFObjectHandle obj = info.getKey(key);
            return obj.isString() ? obj.getUTF8Value() : "";
        };
        model.metadata.title = get_string("/Title");
        model.metadata.author = get_string("/Author");
        model.metadata.creator = get_string("/Creator");
        model.metadata.producer = get_string("/Producer");
    }

    int idx = 1;
    for (auto& page : pages) {
        PageModel pm;
        pm.number = idx++;
        pm.rotation = page.getAttribute("/Rotate", false).getIntValueAsInt();
        
        // Boxes
        pm.media_box = qpdf_rect_to_pg_rect(page.getMediaBox());
        pm.trim_box = qpdf_rect_to_pg_rect(page.getTrimBox());
        pm.bleed_box = qpdf_rect_to_pg_rect(page.getBleedBox());
        pm.crop_box = qpdf_rect_to_pg_rect(page.getCropBox());
        
        model.pages.push_back(pm);
    }

    PG_LOG_INFO("Successfully extracted PDF data: {} pages", model.page_count);
    return model;
}

} // namespace printguard::pdf
