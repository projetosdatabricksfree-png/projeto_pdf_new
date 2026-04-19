#include "printguard/domain/finding.hpp"

namespace printguard::domain {

bool Finding::is_blocking() const {
    return severity == FindingSeverity::ERROR;
}

std::string to_string(FindingSeverity severity) {
    switch (severity) {
        case FindingSeverity::INFO:
            return "INFO";
        case FindingSeverity::WARNING:
            return "WARNING";
        case FindingSeverity::ERROR:
            return "ERROR";
    }
    return "WARNING";
}

std::string to_string(Fixability fixability) {
    switch (fixability) {
        case Fixability::NONE:
            return "None";
        case Fixability::AUTOMATIC_SAFE:
            return "AutomaticSafe";
        case Fixability::AUTOMATIC_RISKY:
            return "AutomaticRisky";
    }
    return "None";
}

} // namespace printguard::domain
