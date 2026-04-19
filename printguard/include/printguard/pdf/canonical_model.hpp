#pragma once

#include <string>
#include <vector>
#include <map>

namespace printguard::pdf {

struct Rect {
    double x = 0;
    double y = 0;
    double w = 0;
    double h = 0;
};

struct PageModel {
    int number;
    Rect media_box;
    Rect trim_box;
    Rect bleed_box;
    Rect crop_box;
    int rotation; // 0, 90, 180, 270
    std::vector<std::string> fonts;
};

struct DocumentMetadata {
    std::string title;
    std::string author;
    std::string creator;
    std::string producer;
    std::string pdf_version;
    bool is_encrypted = false;
    bool is_linearized = false;
};

struct DocumentModel {
    DocumentMetadata metadata;
    std::vector<PageModel> pages;
    int page_count = 0;
};

} // namespace printguard::pdf
