#include "printguard/fix/fixes/attach_output_intent_fix.hpp"

#include "../pdf_color_utils.hpp"

#include <qpdf/QPDFObjectHandle.hh>

namespace printguard::fix {

std::string AttachOutputIntentFix::id() const {
    return "AttachOutputIntentFix";
}

std::string AttachOutputIntentFix::targets_finding_code() const {
    return "PG_ERR_MISSING_OUTPUT_INTENT";
}

domain::FixRecord AttachOutputIntentFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    QPDFObjectHandle root = ctx.pdf.getRoot();
    QPDFObjectHandle existing = root.getKey("/OutputIntents");
    if (existing.isArray() && existing.getArrayNItems() > 0) {
        record.success = false;
        record.message = "O documento ja possui Output Intent no catalogo.";
        record.details["profile_attached"] = "none";
        record.details["profile_stream_bytes"] = "0";
        record.details["scope"] = "document";
        return record;
    }

    std::string profile_name = resolve_output_icc_profile_name(ctx.preset);
    std::vector<unsigned char> profile_bytes = load_output_icc_profile_bytes(ctx.preset);
    QPDFObjectHandle profile_stream =
        ctx.pdf.makeIndirectObject(ctx.pdf.newStream(to_binary_string(profile_bytes)));
    profile_stream.getDict().replaceKey("/N", QPDFObjectHandle::newInteger(4));
    profile_stream.getDict().replaceKey("/Alternate", QPDFObjectHandle::newName("/DeviceCMYK"));

    QPDFObjectHandle output_intent = QPDFObjectHandle::newDictionary();
    output_intent.replaceKey("/Type", QPDFObjectHandle::newName("/OutputIntent"));
    output_intent.replaceKey("/S", QPDFObjectHandle::newName("/GTS_PDFX"));
    output_intent.replaceKey(
        "/OutputConditionIdentifier", QPDFObjectHandle::newString(profile_name));
    output_intent.replaceKey("/Info", QPDFObjectHandle::newString(profile_name));
    output_intent.replaceKey("/DestOutputProfile", profile_stream);
    QPDFObjectHandle output_intent_ref = ctx.pdf.makeIndirectObject(output_intent);

    QPDFObjectHandle output_intents = existing;
    if (!output_intents.isArray()) {
        output_intents = QPDFObjectHandle::newArray();
        root.replaceKey("/OutputIntents", output_intents);
    }
    output_intents.appendItem(output_intent_ref);

    record.success = true;
    record.message = "Perfil de cor de saida (Output Intent) CMYK adicionado ao arquivo.";
    record.details["profile_attached"] = profile_name;
    record.details["profile_stream_bytes"] = std::to_string(profile_bytes.size());
    record.details["scope"] = "document";

    return record;
}

} // namespace printguard::fix
