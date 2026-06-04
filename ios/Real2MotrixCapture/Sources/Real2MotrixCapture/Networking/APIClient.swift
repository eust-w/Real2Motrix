import Foundation

final class APIClient {
    var baseURL: URL
    private let session: URLSession
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        encoder.keyEncodingStrategy = .convertToSnakeCase
    }

    func health() async throws {
        let (_, response) = try await session.data(from: baseURL.appending(path: "/api/health"))
        try validate(response)
    }

    func projects() async throws -> [Project] {
        let (data, response) = try await session.data(from: baseURL.appending(path: "/api/projects"))
        try validate(response)
        return try decoder.decode(ProjectListResponse.self, from: data).projects
    }

    func createProject(name: String, description: String) async throws -> Project {
        var request = URLRequest(url: baseURL.appending(path: "/api/projects"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(ProjectCreateRequest(name: name, description: description, sourceType: "ios_capture"))
        let (data, response) = try await session.data(for: request)
        try validate(response)
        return try decoder.decode(Project.self, from: data)
    }

    func job(id: String) async throws -> JobStatus {
        let (data, response) = try await session.data(from: baseURL.appending(path: "/api/jobs/\(id)"))
        try validate(response)
        return try decoder.decode(JobStatus.self, from: data)
    }

    private func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
    }
}

