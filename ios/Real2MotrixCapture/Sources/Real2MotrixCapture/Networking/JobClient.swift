import Foundation

final class JobClient {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func poll(jobId: String, intervalSeconds: UInt64 = 2, onUpdate: @escaping (JobStatus) -> Void) async throws {
        while true {
            let status = try await apiClient.job(id: jobId)
            await MainActor.run {
                onUpdate(status)
            }
            if ["completed", "failed"].contains(status.status) {
                return
            }
            try await Task.sleep(nanoseconds: intervalSeconds * 1_000_000_000)
        }
    }
}

