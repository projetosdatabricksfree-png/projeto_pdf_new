#pragma once

#include "printguard/domain/preset.hpp"

#include <filesystem>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <string>
#include <vector>

namespace printguard::fix {

std::filesystem::path resolve_output_icc_profile_path(const domain::ProductPreset& preset);
std::string resolve_output_icc_profile_name(const domain::ProductPreset& preset);
std::vector<unsigned char> load_output_icc_profile_bytes(const domain::ProductPreset& preset);

int get_integer(QPDFObjectHandle dict, const std::string& key, int fallback = 0);
QPDFObjectHandle resolve_image_colorspace(
    QPDFPageObjectHelper& page,
    QPDFObjectHandle image_dict,
    std::string* resolved_name = nullptr);
bool is_rgb_image_colorspace(QPDFObjectHandle color_space);
bool is_device_cmyk_colorspace(QPDFObjectHandle color_space);
std::vector<unsigned char> read_stream_bytes(QPDFObjectHandle stream);
std::string to_binary_string(const std::vector<unsigned char>& bytes);

} // namespace printguard::fix
