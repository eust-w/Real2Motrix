import Foundation

struct Project: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let description: String
    let sourceType: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case sourceType = "source_type"
        case status
    }
}

struct ProjectListResponse: Codable {
    let projects: [Project]
}

struct ProjectCreateRequest: Codable {
    let name: String
    let description: String
    let sourceType: String

    enum CodingKeys: String, CodingKey {
        case name
        case description
        case sourceType = "source_type"
    }
}

