import CoreImage
import UIKit

enum ImageUtils {
    static let context = CIContext()

    static func jpegData(from pixelBuffer: CVPixelBuffer, quality: CGFloat = 0.86) -> Data? {
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return nil }
        return UIImage(cgImage: cgImage).jpegData(compressionQuality: quality)
    }

    static func pngData(from pixelBuffer: CVPixelBuffer) -> Data? {
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        return context.pngRepresentation(of: ciImage, format: .RGBA8, colorSpace: CGColorSpaceCreateDeviceRGB())
    }

    static func brightness(from pixelBuffer: CVPixelBuffer) -> Double {
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, 0) else { return 0 }
        let width = CVPixelBufferGetWidthOfPlane(pixelBuffer, 0)
        let height = CVPixelBufferGetHeightOfPlane(pixelBuffer, 0)
        let bytesPerRow = CVPixelBufferGetBytesPerRowOfPlane(pixelBuffer, 0)
        let bytes = base.assumingMemoryBound(to: UInt8.self)
        var total = 0
        let step = max(1, width * height / 4_000)
        var count = 0
        var index = 0
        for y in 0..<height {
            let row = bytes + y * bytesPerRow
            for x in 0..<width where index % step == 0 {
                total += Int(row[x])
                count += 1
            }
            index += width
        }
        return count == 0 ? 0 : Double(total) / Double(count) / 255.0
    }

    static func blurScore(from pixelBuffer: CVPixelBuffer) -> Double {
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, 0) else { return 0 }
        let width = CVPixelBufferGetWidthOfPlane(pixelBuffer, 0)
        let height = CVPixelBufferGetHeightOfPlane(pixelBuffer, 0)
        let bytesPerRow = CVPixelBufferGetBytesPerRowOfPlane(pixelBuffer, 0)
        let bytes = base.assumingMemoryBound(to: UInt8.self)
        var values: [Double] = []
        let step = max(2, min(width, height) / 80)
        for y in Swift.stride(from: step, to: height - step, by: step) {
            let row = bytes + y * bytesPerRow
            let up = bytes + (y - step) * bytesPerRow
            let down = bytes + (y + step) * bytesPerRow
            for x in Swift.stride(from: step, to: width - step, by: step) {
                let lap = Double(up[x]) + Double(down[x]) + Double(row[x - step]) + Double(row[x + step]) - 4.0 * Double(row[x])
                values.append(lap)
            }
        }
        guard !values.isEmpty else { return 0 }
        let mean = values.reduce(0, +) / Double(values.count)
        return values.reduce(0) { $0 + pow($1 - mean, 2) } / Double(values.count)
    }
}
