// ocr_macos.swift — OCR selected PDF pages with the macOS Vision framework.
//
// Usage: ocr_macos <file.pdf> <pages: "1,2,5"> [languages: "en-US,fr-FR"]
// Output: JSON object {"1": "text…", "2": "text…"} on stdout.
//
// Called by pdf_lib.ocr_pages(); compiled once into the cache by pdf_lib._vision_binary().

import Foundation
import PDFKit
import Vision
import AppKit

func fail(_ msg: String) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 3 else { fail("usage: ocr_macos <file.pdf> <pages> [languages]") }
guard let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else { fail("cannot open PDF") }
let pages = args[2].split(separator: ",").compactMap { Int($0) }
let languages = args.count >= 4 ? args[3].split(separator: ",").map(String.init) : []

func render(_ page: PDFPage, scale: CGFloat = 3.0) -> CGImage? {
    let box = page.bounds(for: .mediaBox)
    let w = Int(box.width * scale), h = Int(box.height * scale)
    guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                              space: CGColorSpaceCreateDeviceRGB(),
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    ctx.translateBy(x: -box.origin.x, y: -box.origin.y)
    page.draw(with: .mediaBox, to: ctx)
    return ctx.makeImage()
}

var result: [String: String] = [:]
for n in pages {
    guard n >= 1, n <= doc.pageCount, let page = doc.page(at: n - 1), let img = render(page) else {
        result[String(n)] = ""; continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    if !languages.isEmpty { req.recognitionLanguages = languages }
    else if #available(macOS 13.0, *) { req.automaticallyDetectsLanguage = true }
    do { try VNImageRequestHandler(cgImage: img, options: [:]).perform([req]) }
    catch { result[String(n)] = ""; continue }
    // Sort top-to-bottom, then left-to-right (Vision origin is bottom-left).
    let obs = (req.results ?? []).sorted {
        abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.01
            ? $0.boundingBox.midY > $1.boundingBox.midY
            : $0.boundingBox.minX < $1.boundingBox.minX
    }
    // Join observations on the same visual line with spaces.
    var lines: [String] = []
    var lastY: CGFloat? = nil
    for o in obs {
        guard let s = o.topCandidates(1).first?.string else { continue }
        if let y = lastY, abs(y - o.boundingBox.midY) <= 0.01, !lines.isEmpty {
            lines[lines.count - 1] += "  " + s
        } else { lines.append(s) }
        lastY = o.boundingBox.midY
    }
    result[String(n)] = lines.joined(separator: "\n")
}

let data = try! JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
FileHandle.standardOutput.write(data)
