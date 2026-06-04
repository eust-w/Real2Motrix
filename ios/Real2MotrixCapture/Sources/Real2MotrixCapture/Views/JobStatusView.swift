import SwiftUI

struct JobStatusView: View {
    @EnvironmentObject private var state: AppState
    let job: JobStatus

    var displayedJob: JobStatus {
        state.jobStatus ?? job
    }

    var body: some View {
        Form {
            Section("Status") {
                LabeledContent("State", value: displayedJob.status)
                ProgressView(value: displayedJob.progress, total: 100)
                LabeledContent("Step", value: displayedJob.currentStep)
                if let error = displayedJob.errorMessage {
                    Text(error).foregroundStyle(.red)
                }
            }
        }
        .navigationTitle("Job")
    }
}
