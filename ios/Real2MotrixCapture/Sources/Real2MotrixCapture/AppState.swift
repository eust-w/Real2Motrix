import Foundation
import SwiftUI

@MainActor
final class AppState: ObservableObject {
    @Published var serverURLText = ""
    @Published var connectionMessage = "Not connected"
    @Published var projects: [Project] = []
    @Published var selectedProject: Project?
    @Published var captureType: CaptureType = .scene
    @Published var captureMode: CaptureMode = .arkitPose
    @Published var lastZipURL: URL?
    @Published var jobStatus: JobStatus?
    @Published var isBusy = false

    var apiClient: APIClient? {
        guard let url = URL(string: serverURLText) else { return nil }
        return APIClient(baseURL: url)
    }

    func testConnection() async {
        guard let client = apiClient else {
            connectionMessage = "Invalid backend URL"
            return
        }
        do {
            try await client.health()
            projects = try await client.projects()
            connectionMessage = "Connected"
        } catch {
            connectionMessage = "Backend unreachable: \(error.localizedDescription)"
        }
    }

    func createProject(name: String) async {
        guard let client = apiClient else { return }
        do {
            let project = try await client.createProject(name: name, description: "Captured from iOS")
            selectedProject = project
            projects = try await client.projects()
        } catch {
            connectionMessage = "Create project failed: \(error.localizedDescription)"
        }
    }

    func upload(zipURL: URL, hasLidar: Bool) async {
        guard let client = apiClient, let project = selectedProject else { return }
        isBusy = true
        defer { isBusy = false }
        do {
            let response = try await UploadClient(apiClient: client).uploadCapture(
                projectId: project.id,
                zipURL: zipURL,
                captureType: captureType,
                captureMode: captureMode,
                deviceModel: DeviceUtils.deviceModel,
                hasLidar: hasLidar
            )
            jobStatus = response.job
            try await JobClient(apiClient: client).poll(jobId: response.job.id) { [weak self] status in
                self?.jobStatus = status
            }
        } catch {
            connectionMessage = "Upload failed: \(error.localizedDescription)"
        }
    }
}
