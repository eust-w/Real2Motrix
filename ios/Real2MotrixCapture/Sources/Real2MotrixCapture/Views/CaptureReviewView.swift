import SwiftUI

struct CaptureReviewView: View {
    @EnvironmentObject private var state: AppState
    let zipURL: URL
    let hasLidar: Bool

    var body: some View {
        Form {
            Section("Package") {
                LabeledContent("File", value: zipURL.lastPathComponent)
                LabeledContent("Path", value: zipURL.path)
            }
            Section {
                NavigationLink("Upload", destination: UploadProgressView(zipURL: zipURL, hasLidar: hasLidar))
            }
        }
        .navigationTitle("Review")
    }
}

