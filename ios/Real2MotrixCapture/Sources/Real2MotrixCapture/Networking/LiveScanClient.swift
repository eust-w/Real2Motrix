import Foundation

final class LiveScanClient {
    private let apiClient: APIClient
    private let decoder = JSONDecoder()

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func createSession(
        projectId: String,
        captureType: CaptureType,
        captureMode: CaptureMode,
        deviceModel: String,
        hasLidar: Bool
    ) async throws -> LiveScanSessionRecord {
        var request = URLRequest(url: apiClient.baseURL.appending(path: "/api/projects/\(projectId)/live-sessions"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "capture_type": captureType.rawValue,
            "capture_mode": captureMode.rawValue,
            "target_type": captureType == .object ? "object" : "scene",
            "device_model": deviceModel,
            "has_lidar": hasLidar
        ])
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try decoder.decode(LiveScanSessionRecord.self, from: data)
    }

    func uploadFrame(
        projectId: String,
        sessionId: String,
        frameIndex: Int,
        timestamp: TimeInterval,
        imageData: Data,
        poseJSON: String,
        qualityJSON: String,
        intrinsicsJSON: String
    ) async throws -> LiveScanSessionRecord {
        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: apiClient.baseURL.appending(path: "/api/projects/\(projectId)/live-sessions/\(sessionId)/frames"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = multipartBody(
            boundary: boundary,
            fields: [
                "frame_index": "\(frameIndex)",
                "timestamp": "\(timestamp)",
                "pose_json": poseJSON,
                "quality_json": qualityJSON,
                "intrinsics_json": intrinsicsJSON
            ],
            fileName: "frame_\(String(format: "%06d", frameIndex)).jpg",
            imageData: imageData
        )
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try decoder.decode(LiveScanSessionRecord.self, from: data)
    }

    func finish(projectId: String, sessionId: String) async throws -> LiveScanFinishResponse {
        var request = URLRequest(url: apiClient.baseURL.appending(path: "/api/projects/\(projectId)/live-sessions/\(sessionId)/finish"))
        request.httpMethod = "POST"
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try decoder.decode(LiveScanFinishResponse.self, from: data)
    }

    func uploadMeshChunk(projectId: String, sessionId: String, chunkIndex: Int, objData: Data) async throws -> LiveScanSessionRecord {
        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: apiClient.baseURL.appending(path: "/api/projects/\(projectId)/live-sessions/\(sessionId)/mesh-chunks"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = meshMultipartBody(boundary: boundary, chunkIndex: chunkIndex, objData: objData)
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try decoder.decode(LiveScanSessionRecord.self, from: data)
    }

    private func multipartBody(boundary: String, fields: [String: String], fileName: String, imageData: Data) -> Data {
        var data = Data()
        for (key, value) in fields {
            data.appendMultipartString("--\(boundary)\r\n")
            data.appendMultipartString("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n")
            data.appendMultipartString("\(value)\r\n")
        }
        data.appendMultipartString("--\(boundary)\r\n")
        data.appendMultipartString("Content-Disposition: form-data; name=\"frame\"; filename=\"\(fileName)\"\r\n")
        data.appendMultipartString("Content-Type: image/jpeg\r\n\r\n")
        data.append(imageData)
        data.appendMultipartString("\r\n--\(boundary)--\r\n")
        return data
    }

    private func meshMultipartBody(boundary: String, chunkIndex: Int, objData: Data) -> Data {
        var data = Data()
        data.appendMultipartString("--\(boundary)\r\n")
        data.appendMultipartString("Content-Disposition: form-data; name=\"chunk_index\"\r\n\r\n")
        data.appendMultipartString("\(chunkIndex)\r\n")
        data.appendMultipartString("--\(boundary)\r\n")
        data.appendMultipartString("Content-Disposition: form-data; name=\"mesh\"; filename=\"mesh_snapshot.obj\"\r\n")
        data.appendMultipartString("Content-Type: model/obj\r\n\r\n")
        data.append(objData)
        data.appendMultipartString("\r\n--\(boundary)--\r\n")
        return data
    }

    private func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
    }
}

private extension Data {
    mutating func appendMultipartString(_ string: String) {
        append(Data(string.utf8))
    }
}
