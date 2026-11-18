// Encodes <frames dir>/f0000.png… into an H.264 .mov at 30 fps — run by tools/build-header.py.
import AVFoundation
import AppKit
import CoreVideo

let args = CommandLine.arguments
let dir = URL(fileURLWithPath: args[1]), out = URL(fileURLWithPath: args[2])
let width = 3840, height = 1646, fps: Int32 = 30
try? FileManager.default.removeItem(at: out)

let frames = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension == "png" }.sorted { $0.lastPathComponent < $1.lastPathComponent }

let writer = try AVAssetWriter(outputURL: out, fileType: .mov)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: width, AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 30_000_000,
                                      AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
                                      AVVideoMaxKeyFrameIntervalKey: 30],
    AVVideoColorPropertiesKey: [AVVideoColorPrimariesKey: AVVideoColorPrimaries_ITU_R_709_2,
                                AVVideoTransferFunctionKey: AVVideoTransferFunction_ITU_R_709_2,
                                AVVideoYCbCrMatrixKey: AVVideoYCbCrMatrix_ITU_R_709_2],
])
input.expectsMediaDataInRealTime = false
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
    kCVPixelBufferWidthKey as String: width, kCVPixelBufferHeightKey as String: height,
])
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

for (i, url) in frames.enumerated() {
    while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.005) }
    guard let image = NSImage(contentsOf: url)?.cgImage(forProposedRect: nil, context: nil, hints: nil),
          let pool = adaptor.pixelBufferPool else { fatalError("frame \(i)") }
    var buffer: CVPixelBuffer?
    CVPixelBufferPoolCreatePixelBuffer(nil, pool, &buffer)
    guard let buffer else { fatalError("buffer \(i)") }
    CVPixelBufferLockBaseAddress(buffer, [])
    let context = CGContext(data: CVPixelBufferGetBaseAddress(buffer), width: width, height: height,
                            bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
                            space: CGColorSpace(name: CGColorSpace.sRGB)!,
                            bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
    context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
    CVPixelBufferUnlockBaseAddress(buffer, [])
    adaptor.append(buffer, withPresentationTime: CMTime(value: CMTimeValue(i), timescale: fps))
}
input.markAsFinished()
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()
print(writer.status == .completed ? "wrote \(frames.count) frames to \(out.path)" : "failed: \(String(describing: writer.error))")
