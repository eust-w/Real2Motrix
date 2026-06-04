import SwiftUI

struct UploadProgressView: View {
    @EnvironmentObject private var state: AppState
    let zipURL: URL
    let hasLidar: Bool

    var body: some View {
        Form {
            Section("Upload") {
                Button(state.isBusy ? "Uploading..." : "Upload capture_session.zip") {
                    Task { await state.upload(zipURL: zipURL, hasLidar: hasLidar) }
                }
                .disabled(state.isBusy)
            }
            if let job = state.jobStatus {
                Section("Job") {
                    NavigationLink("Job status", destination: JobStatusView(job: job))
                }
            }
        }
        .navigationTitle("Upload")
    }
}

