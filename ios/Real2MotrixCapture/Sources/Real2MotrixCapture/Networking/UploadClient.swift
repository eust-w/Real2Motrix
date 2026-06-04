import Foundation

final class UploadClient {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func uploadCapture(projectId: String, zipURL: URL, captureType: CaptureType, captureMode: CaptureMode, deviceModel: String, hasLidar: Bool) async throws -> CaptureSessionUploadResponse {
        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: apiClient.baseURL.appending(path: "/api/projects/\(projectId)/capture-sessions"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = try multipartBody(
            boundary: boundary,
            fields: [
                "capture_type": captureType.rawValue,
                "capture_mode": captureMode.rawValue,
                "device_type": deviceModel,
                "has_lidar": hasLidar ? "true" : "false"
            ],
            fileField: "file",
            fileURL: zipURL,
            mimeType: "application/zip"
        )
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(CaptureSessionUploadResponse.self, from: data)
    }

    private func multipartBody(boundary: String, fields: [String: String], fileField: String, fileURL: URL, mimeType: String) throws -> Data {
        var data = Data()
        for (key, value) in fields {
            data.appendString("--\(boundary)\r\n")
            data.appendString("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n")
            data.appendString("\(value)\r\n")
        }
        data.appendString("--\(boundary)\r\n")
        data.appendString("Content-Disposition: form-data; name=\"\(fileField)\"; filename=\"capture_session.zip\"\r\n")
        data.appendString("Content-Type: \(mimeType)\r\n\r\n")
        data.append(try Data(contentsOf: fileURL))
        data.appendString("\r\n--\(boundary)--\r\n")
        return data
    }
}

private extension Data {
    mutating func appendString(_ string: String) {
        append(Data(string.utf8))
    }
}

