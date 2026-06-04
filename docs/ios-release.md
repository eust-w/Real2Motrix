# iOS Release Management

Real2MotrixCapture is generated from `ios/Real2MotrixCapture/project.yml` with XcodeGen.

## Current Local Build Status

The local machine is not currently able to build the iOS app with `xcodebuild` because `xcode-select` points to Command Line Tools:

```text
xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer directory '/Library/Developer/CommandLineTools' is a command line tools instance
```

Install/select full Xcode locally to build on this Mac:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

## GitHub Actions

Two workflows manage iOS builds:

- `.github/workflows/ios-ci.yml`: builds the app for iOS Simulator on PRs and pushes to `main`.
- `.github/workflows/ios-release.yml`: builds a signed `.ipa`, uploads workflow artifacts, and publishes a GitHub Release.

The release workflow runs when:

- a tag matching `ios-v*` is pushed, for example `ios-v0.1.0`;
- it is manually triggered from GitHub Actions with a version input.

## Required GitHub Secrets

Configure these repository secrets before running `iOS Release`:

- `IOS_TEAM_ID`: Apple Developer Team ID.
- `IOS_DISTRIBUTION_CERTIFICATE_BASE64`: base64 encoded `.p12` signing certificate.
- `IOS_DISTRIBUTION_CERTIFICATE_PASSWORD`: password for the `.p12` certificate.
- `IOS_PROVISIONING_PROFILE_BASE64`: base64 encoded `.mobileprovision` profile matching the bundle identifier.

Optional repository variable:

- `IOS_BUNDLE_IDENTIFIER`: bundle id for release signing. Defaults to `local.real2motrix.capture`.

## Encoding Signing Files

```bash
base64 -i ios_distribution.p12 | pbcopy
base64 -i Real2MotrixCapture.mobileprovision | pbcopy
```

Paste each value into the matching GitHub secret.

## Release Commands

Create a tag-driven release:

```bash
git tag ios-v0.1.0
git push origin ios-v0.1.0
```

Or run `iOS Release` manually in GitHub Actions and enter `0.1.0`.

The workflow creates release assets:

- `Real2MotrixCapture-ios-v<version>.ipa`
- `Real2MotrixCapture-ios-v<version>.xcarchive.zip`
