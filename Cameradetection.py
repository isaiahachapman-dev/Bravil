import matplotlib.pyplot as plt
import cv2 as cv
import numpy as np
import os
import sys

PLATE = {
    6:  {"rows": 2, "cols": 3, "spacingMm": 39.12},
    12: {"rows": 3, "cols": 4, "spacingMm": 26.01},
}

bedWidthMm = 619


def findBed(gray):
    h, w = gray.shape
    _, bw = cv.threshold(gray, 50, 255, cv.THRESH_BINARY_INV)
    contours, _ = cv.findContours(bw, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv.contourArea, reverse=True)
    bars = []
    for cnt in contours[:5]:
        x, y, cw, ch = cv.boundingRect(cnt)
        if ch > h * 0.5:
            bars.append((x, y, cw, ch))
    bars.sort(key=lambda b: b[0])
    if len(bars) >= 2:
        return bars[0][0] + bars[0][2], bars[-1][0]
    return 0, w


def detectCircles(gray, minDist, minR, maxR):
    bilat = cv.bilateralFilter(gray, 9, 75, 75)
    enhanced = cv.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8)).apply(bilat)

    strict = cv.HoughCircles(enhanced, cv.HOUGH_GRADIENT, 1.0, minDist,
        param1=70, param2=35, minRadius=int(minR * 1.3), maxRadius=maxR)

    if strict is not None:
        c = np.round(strict[0]).astype(int)
        radii = c[:, 2]
        med = np.median(radii)
        filtered = c[np.abs(radii - med) / med < 0.15]
        if len(filtered) >= 4:
            return filtered, enhanced, "strict"

    relaxed = cv.HoughCircles(enhanced, cv.HOUGH_GRADIENT, 1.0, minDist,
        param1=70, param2=22, minRadius=minR, maxRadius=maxR)

    if relaxed is not None:
        return np.round(relaxed[0]).astype(int), enhanced, "relaxed"

    return np.array([]), enhanced, "none"


def filterRadius(circles):
    if len(circles) < 3:
        return circles
    radii = circles[:, 2]
    median = np.median(radii)
    return circles[np.abs(radii - median) / median < 0.25]


def clusterDensest(circles, targetCount):
    if len(circles) <= targetCount:
        return circles
    best = circles.copy()
    bestScore = 0
    bestSet = circles.copy()
    for _ in range(len(circles)):
        if len(best) < 4:
            break
        cen = best[:, :2].astype(float)
        centroid = cen.mean(axis=0)
        xRange = cen[:, 0].max() - cen[:, 0].min()
        yRange = cen[:, 1].max() - cen[:, 1].min()
        density = len(best) / max(1, xRange * yRange) * 10000
        score = len(best) * density
        if score > bestScore and len(best) >= targetCount:
            bestScore = score
            bestSet = best.copy()
        dists = np.linalg.norm(cen - centroid, axis=1)
        best = np.delete(best, dists.argmax(), axis=0)
    return bestSet


def sortToGrid(circles):
    if len(circles) == 0:
        return circles, 0, 0
    byY = circles[np.argsort(circles[:, 1])]
    rows = [[byY[0]]]
    for c in byY[1:]:
        if abs(int(c[1]) - int(rows[-1][-1][1])) < 60:
            rows[-1].append(c)
        else:
            rows.append([c])
    result = []
    for row in rows:
        result.extend(sorted(row, key=lambda x: int(x[0])))
    return np.array(result), len(rows), max(len(r) for r in rows)


def drawCircles(img, circles, color=(0, 255, 0)):
    vis = img.copy() if len(img.shape) == 3 else cv.cvtColor(img, cv.COLOR_GRAY2BGR)
    for c in circles:
        cv.circle(vis, (int(c[0]), int(c[1])), int(c[2]), color, 2)
        cv.circle(vis, (int(c[0]), int(c[1])), 3, (0, 0, 255), -1)
    return vis


def printDistances(circles, nCols, mmPerPx):
    print("\nNearest neighbor distances:")
    for i in range(len(circles)):
        label = chr(65 + i // nCols) + str((i % nCols) + 1)
        bestDist = float('inf')
        bestLabel = ""
        for j in range(len(circles)):
            if i == j:
                continue
            dx = float(circles[j][0] - circles[i][0]) * mmPerPx
            dy = float(circles[j][1] - circles[i][1]) * mmPerPx
            d = np.sqrt(dx * dx + dy * dy)
            other = chr(65 + j // nCols) + str((j % nCols) + 1)
            if d < bestDist:
                bestDist = d
                bestLabel = other
        print("  {} -> {}: {:.1f}mm".format(label, bestLabel, bestDist))

    print("\nAll pairwise (< 50mm):")
    for i in range(len(circles)):
        for j in range(i + 1, len(circles)):
            dx = float(circles[j][0] - circles[i][0]) * mmPerPx
            dy = float(circles[j][1] - circles[i][1]) * mmPerPx
            d = np.sqrt(dx * dx + dy * dy)
            if d < 50:
                li = chr(65 + i // nCols) + str((i % nCols) + 1)
                lj = chr(65 + j // nCols) + str((j % nCols) + 1)
                print("  {} <-> {}: {:.1f}mm (dx={:.1f}, dy={:.1f})".format(li, lj, d, dx, dy))


def main():
    if len(sys.argv) > 1:
        imagePath = sys.argv[1]
    else:
        imagePath = r"C:\Users\Sp00k\Downloads\drive-download-20260409T184405Z-3-001\test24.jpg"

    if not os.path.isfile(imagePath):
        print("File not found: {}".format(imagePath))
        sys.exit(1)

    img = cv.imread(imagePath)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    bedLeft, bedRight = findBed(gray)
    bedWidth = bedRight - bedLeft
    mmPerPx = bedWidthMm / max(1, bedWidth)
    scale = bedWidth / 886.0
    minR = max(10, int(25 * scale))
    maxR = max(30, int(80 * scale))
    minDist = max(30, int(70 * scale))

    print("Bed: {}..{} ({}px), {:.4f} mm/px".format(bedLeft, bedRight, bedWidth, mmPerPx))

    crop = img[:, bedLeft:bedRight]
    cropGray = gray[:, bedLeft:bedRight]

    # Step 1: detect
    rawCircles, processed, pipeline = detectCircles(cropGray, minDist, minR, maxR)
    print("\n1. HCT ({}): {} circles".format(pipeline, len(rawCircles)))

    # Step 2: radius filter
    afterRadius = filterRadius(rawCircles)
    print("2. Radius filter: {} circles".format(len(afterRadius)))

    # Step 3: density cluster
    targetCount = 12 if len(afterRadius) > 8 else 6
    afterCluster = clusterDensest(afterRadius, targetCount)
    print("3. Density cluster (target {}): {} circles".format(targetCount, len(afterCluster)))

    # Step 4: sort
    final, nRows, nCols = sortToGrid(afterCluster)
    if nRows == 3 and nCols == 2:
        nCols = 2
    elif nRows >= 4:
        nCols = max(len([c for c in final if abs(int(c[1]) - int(final[0][1])) < 60]), 3)

    plateType = 12 if len(final) > 8 else (6 if len(final) >= 4 else None)
    print("4. Sorted: {} rows x {} cols = {}-well\n".format(nRows, nCols, plateType or "?"))

    for i, c in enumerate(final):
        label = "{}{}".format(chr(65 + i // nCols), (i % nCols) + 1)
        mmX = c[0] * mmPerPx
        mmY = c[1] * mmPerPx
        rMm = c[2] * mmPerPx
        print("  {}  px({:4d},{:4d})  mm({:6.1f},{:6.1f})  r={:.1f}mm".format(
            label, c[0], c[1], mmX, mmY, rMm))

    printDistances(final, nCols, mmPerPx)

    # Debug figure
    edges = cv.Canny(processed, 50, 150)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle("{}-well detection ({})".format(plateType or "?", pipeline), fontsize=14)

    axes[0, 0].imshow(cv.cvtColor(crop, cv.COLOR_BGR2RGB))
    axes[0, 0].set_title("1. Bed crop")

    axes[0, 1].imshow(processed, cmap='gray')
    axes[0, 1].set_title("2. Preprocessed")

    axes[0, 2].imshow(edges, cmap='gray')
    axes[0, 2].set_title("3. Canny edges")

    axes[1, 0].imshow(cv.cvtColor(drawCircles(crop, rawCircles, (255, 0, 0)), cv.COLOR_BGR2RGB))
    axes[1, 0].set_title("4. Raw HCT ({})".format(len(rawCircles)))

    axes[1, 1].imshow(cv.cvtColor(drawCircles(crop, afterRadius, (0, 165, 255)), cv.COLOR_BGR2RGB))
    axes[1, 1].set_title("5. Radius filtered ({})".format(len(afterRadius)))

    finalVis = crop.copy()
    for i, c in enumerate(final):
        label = "{}{}".format(chr(65 + i // nCols), (i % nCols) + 1)
        cv.circle(finalVis, (c[0], c[1]), c[2], (0, 255, 0), 2)
        cv.circle(finalVis, (c[0], c[1]), 3, (0, 0, 255), -1)
        cv.putText(finalVis, label, (c[0] - 12, c[1] - c[2] - 6),
                   cv.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
    axes[1, 2].imshow(cv.cvtColor(finalVis, cv.COLOR_BGR2RGB))
    axes[1, 2].set_title("6. Final ({})".format(len(final)))

    for ax in axes.flat:
        ax.axis('off')
    plt.tight_layout()
    plt.show()


main()