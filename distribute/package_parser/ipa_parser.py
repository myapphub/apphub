#!/usr/bin/env python
# -*- coding: utf-8 -*-

import plistlib
import re
import zipfile
from struct import pack, unpack
from zlib import compress, crc32, decompress

from application.models import Application

from .base import AppParser


def getNormalizedPNG(data):
    pngheader = b"\x89PNG\r\n\x1a\n"
    oldPNG = data

    if oldPNG[:8] != pngheader:
        return None

    newPNG = oldPNG[:8]
    chunkPos = len(newPNG)
    idatAcc = b""
    breakLoop = False

    # For each chunk in the PNG file
    while chunkPos < len(oldPNG):
        skip = False

        # Reading chunk
        chunkLength = oldPNG[chunkPos:chunkPos + 4]
        chunkLength = unpack(">L", chunkLength)[0]
        chunkType = oldPNG[chunkPos + 4 : chunkPos + 8]
        chunkData = oldPNG[chunkPos + 8:chunkPos + 8 + chunkLength]
        chunkCRC = oldPNG[chunkPos + chunkLength + 8:chunkPos + chunkLength + 12]
        chunkCRC = unpack(">L", chunkCRC)[0]
        chunkPos += chunkLength + 12

        # Parsing the header chunk
        if chunkType == b"IHDR":
            width = unpack(">L", chunkData[0:4])[0]
            height = unpack(">L", chunkData[4:8])[0]

        # Parsing the image chunk
        if chunkType == b"IDAT":
            # Store the chunk data for later decompression
            idatAcc += chunkData
            skip = True

        # Removing CgBI chunk
        if chunkType == b"CgBI":
            skip = True

        # Add all accumulated IDATA chunks
        if chunkType == b"IEND":
            try:
                # Uncompressing the image chunk
                bufSize = width * height * 4 + height
                chunkData = decompress(idatAcc, -15, bufSize)
            except:    # noqa: E722
                # The PNG image is normalized
                return None

            chunkType = b"IDAT"

            # Swapping red & blue bytes for each pixel
            newdata = bytearray(b"")

            for y in range(height):
                i = len(newdata)
                newdata.append(chunkData[i])
                for x in range(width):
                    i = len(newdata)
                    newdata.append(chunkData[i + 2])
                    newdata.append(chunkData[i + 1])
                    newdata.append(chunkData[i + 0])
                    newdata.append(chunkData[i + 3])

            # Compressing the image chunk
            chunkData = bytes(newdata)
            chunkData = compress(chunkData)
            chunkLength = len(chunkData)
            chunkCRC = crc32(chunkType)
            chunkCRC = crc32(chunkData, chunkCRC)
            chunkCRC = (chunkCRC + 0x100000000) % 0x100000000
            breakLoop = True

        if not skip:
            newPNG += pack(">L", chunkLength)
            newPNG += chunkType
            if chunkLength > 0:
                newPNG += chunkData
            newPNG += pack(">L", chunkCRC)
        if breakLoop:
            break

    return newPNG


class IpaParser(AppParser):
    @staticmethod
    def can_parse(ext, os=None):
        return ext == "ipa" and (os == Application.OperatingSystem.iOS or os is None)

    def __init__(self, file):
        self.zip = zipfile.ZipFile(file)
        self.__plist = None
        self.__icon = None

    @property
    def os(self):
        return Application.OperatingSystem.iOS

    @property
    def display_name(self):
        return self.plist.get("CFBundleDisplayName")

    @property
    def bundle_name(self):
        return self.plist.get("CFBundleName")

    @property
    def bundle_identifier(self):
        return self.plist.get("CFBundleIdentifier")

    @property
    def version(self):
        return self.plist.get("CFBundleVersion")

    @property
    def short_version(self):
        return self.plist.get("CFBundleShortVersionString")

    @property
    def minimum_os_version(self):
        return self.plist.get("MinimumOSVersion")

    @property
    def app_icon(self):
        if self.__icon:
            return self.__icon

        icons = self.plist.get("CFBundleIcons", {})
        icons = icons.get("CFBundlePrimaryIcon").get("CFBundleIconFiles")
        if len(icons) == 0:
            return None
        icons = sorted(icons, reverse=True)
        pattern = re.compile(r"Payload/[^/]*.app/[^/]*.png")
        for path in self.zip.namelist():
            m = pattern.match(path)
            if m is not None:
                name = path.split("/")[-1]
                if name.startswith(icons[0]) and name.endswith(".png"):
                    self.__icon = self.zip.read(path)
                    data = getNormalizedPNG(self.zip.read(path))
                    if data:
                        self.__icon = data
                    return self.__icon

        return self.__icon

    @property
    def plist(self):
        if self.__plist:
            return self.__plist

        pattern = re.compile(r"Payload/[^/]*.app/Info.plist")
        for path in self.zip.namelist():
            m = pattern.match(path)
            if m is not None:
                # print(m)
                data = self.zip.read(m.group())
                self.__plist = plistlib.loads(data)
        return self.__plist
