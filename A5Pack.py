from struct import pack, unpack, calcsize
import os, argparse

"""ytilitU erawmriF htnysardyH senihcaM dnuoS nuhsA

TODO:
- improve sanitization
- at some point once required: A5 build option. For the time being,
  manually patching raw data is sufficient. There are no checksums,
  signatures whatsoever"""

class A5Pack:
    HDR_FMT = "<6s3s82x"
    HDR_SIZE = calcsize(HDR_FMT)
    INFO_CHUNK_FMT = "<20s20sI"
    INFO_CHUNK_SIZE = calcsize(INFO_CHUNK_FMT)
    HDR_MAGIC = b"A5Pack"
    VALID_CHUNKS = { # Flash dst addr, max valid size
        "A5 code":(0x40020000, 0x200000),
        "A5 voice":(0x40200000, 0x5000000),
        "A5 Reserve1":(0x479C0000, 0x100000),
        "A5 Reserve2":(0x47AC0000, 0x100000),
        "A5 Reserve3":(0x47BC0000, 0x100000),
        "A5 selfcheck":(0x47CC0000, 0x132000),
        "A5 system":(0x47E00000, 0x20000),
        "A5 patch":(0x47F00000, 0x0A5400),
        "A5 patch(5)":(0x47E80000, 0x14A800),
        "stm32 code":(0x8010000, 0x100000),
        "gd32 code":(0x8010000, 0x100000),
        "stm32F030 code":(0x8002800, 0x0D800),
        "gdf32F030 code":(0x8002800, 0x0D800),
        "Z-A5 bootloader":(0x40000000, 0x20000),
        "A5_s code":(0x40020000, 0x132000),
        "A5_s voice":(0x40200000, 0x5000000),
        "A5_s Reserve1":(0x479C0000, 0x100000),
        "A5_s Reserve2":(0x47AC0000, 0x100000),
        "A5_s selfcheck":(0x47CC0000, 0x132000),
        "Z-A5_s bootloader":(0x40000000, 0x20000),
        "A5_3m Reserve1":(0x42600000, 0x100000),
        "A5_3m Reserve2":(0x42700000, 0x100000),
        "A5_3m Reserve3":(0x42800000, 0x100000),
        "A5_3m selfcheck":(0x42900000, 0x132000),
        "A5_3m system":(0x42A40000, 0x20000),
        "A5_3m patch":(0x42200000, 0x200000),
        "A5_7x patch":(0x472C0000, 0x300000),
        "A5_7x multi patch":(0x401E0000, 0x20000),
        "A5_7x lower patch":(0x475C0000, 0x200000),
        "A5_7x upper patch":(0x477C0000, 0x200000)
    }

    def __init__(self, buf):
        self.buf = buf
        if len(buf) < A5Pack.HDR_SIZE:
            raise ValueError("Invalid A5 archive")

        magic, revid = self.read_header()
        if magic != A5Pack.HDR_MAGIC:
            raise ValueError("Invalid A5 archive")

        self.revision = revid[1:].decode("utf-8")
        return

    def get_revision(self):
        return self.revision

    def read_header(self):
        """returns tuple: magic and revision id"""
        return unpack(A5Pack.HDR_FMT, self.buf[:A5Pack.HDR_SIZE])

    def get_first_file(self):
        self.offs_next_info_chunk = A5Pack.HDR_SIZE
        return self._get_file()

    def get_next_file(self):
        return self._get_file()

    def get_raw_data(self, offs, size):
        return self.buf[offs:offs+size]

    def extract_file(self, r, path):
        if r:
            ver, tag, offs, size = r
            name = "%s%s_%08x_%s" % (
                self.revision,
                ver.decode("utf-8").strip("\x00"),
                offs,
                tag.decode("utf-8").strip("\x00").replace(" ", "_"))
            print("Extracting '%s' offs: 0x%x, size: %d" % (name, offs, size))
            f = open(os.path.join(path, name), "wb")
            f.write(self.get_raw_data(offs, size))
            f.close()
        return r is not None

    def _get_file(self):
        try:
            ver, tag, size = self._read_entry(self.offs_next_info_chunk)
        except ValueError:
            return None
            
        offs = self.offs_next_info_chunk + A5Pack.INFO_CHUNK_SIZE
        self.offs_next_info_chunk = offs + size
        return ver, tag, offs, size

    def _read_entry(self, offs):
        """returns tuple: ver, tag, size"""
        if len(self.buf) < offs+A5Pack.INFO_CHUNK_SIZE:
            raise ValueError()
        return unpack(A5Pack.INFO_CHUNK_FMT, self.buf[offs:offs+A5Pack.INFO_CHUNK_SIZE] )


def unpack_A5(filename, path):
    try:
        f = open(filename, "rb")
    except:
        print("Could not open %s" % filename)
        return False

    buf = f.read()
    f.close()

    a5 = A5Pack(buf)

    if not os.path.exists(path):
        os.makedirs(path)

    print("Detected '%s' archive" % a5.get_revision())
    file_idx = 0
    if a5.extract_file(a5.get_first_file(), path):
        file_idx += 1
        while a5.extract_file(a5.get_next_file(), path):
            file_idx += 1
    print("No more files. %d files in total." % (file_idx))
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="filename: A5Pack archive")
    parser.add_argument("-u", "--unpack",
                        action="store_true",
                        help="unpack A5 archive")
    parser.add_argument("-p", "--path",
                        type=str,
                        default="./",
                        help="destination path for -u option")

    args = parser.parse_args()
    if args.unpack:
        print("Unpacking '%s' to destination path '%s'\n" % (args.filename, args.path))
        unpack_A5(args.filename, args.path)
