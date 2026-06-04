import Foundation

struct JobStatus: Codable, Identifiable {
    let id: String
    let projectId: String
    let status: String
    let progress: Double
    let currentStep: String
    let errorMessage: String?

    enum CodingKeys: String, CodingKey {
        case id
        case projectId = "project_id"
        case status
        case progress
        case currentStep = "current_step"
        case errorMessage = "error_message"
    }
}

