from .lsst_warp import LSSTWarper
from scidbpy import interface

SHIM_DEFAULT = 'http://localhost:8080'


class HPXPixels3D(object):
    """
    Class to store and interact with 3D Healpix-projected data

    The three dimensions include two angular dimensions and one time dimension.
    """
    def __init__(self, name=None, input_files=None,
                 cdelt=3, cunit='arcsec', kernel='lanczos2',
                 force_reload=False, interface=None):
        self.name = name
        self.force_reload = force_reload
        self.interface = interface

        if self.interface is None:
            self.interface = self.open_scidb_connection()

        self.warper = LSSTWarper(cdelt=cdelt,
                                 cunit=cunit,
                                 kernel=kernel,
                                 interface=self.interface)

        if (name is not None):
            arr_exists = (name in self.interface.list_arrays())
                
            if force_reload or not arr_exists:
                print "loading into array: {0}".format(self.name)

                # clear the array if needed
                if arr_exists:
                    self.interface.query("remove({0})", name)

                self.arr = None
                self._load_files(input_files)
            else:
                print "using existing array: {0}".format(self.name)
                self.arr = self.interface.wrap_array(self.name)
        else:
            self.arr = None
            self._load_files(input_files)

    @staticmethod
    def open_scidb_connection(address=SHIM_DEFAULT):
        return interface.SciDBShimInterface(address)

    def _load_files(self, files):
        for i, fitsfile in enumerate(files):
            print "- ({0}/{1}) loading {2}".format(i + 1,
                                                   len(files),
                                                   fitsfile)
                                                   
            if self.arr is None:
                self.arr = self.warper.scidb3d_from_fits(fitsfile)
                if self.name is not None:
                    self.arr.rename(self.name, persistent=True)
            else:
                self.interface.query("insert({0}, {1})",
                                     self.warper.scidb3d_from_fits(fitsfile),
                                     self.arr)

    def time_slice(self, time1, time2=None):
        if time2 is None:
            return HPXPixels2D(self, self.arr[:, :, time1])
        else:
            raise NotImplementedError()

    def coadd(self):
        return HPXPixels2D(self, self.arr.sum(2))

    def unique_times(self):
        return self.arr.max((0, 1)).tosparse()['time']


class HPXPixels2D(object):
    """Container for 2D LSST Pixels stored in SciDB"""
    def __init__(self, pix3d, arr):
        self.pix3d = pix3d
        self.arr = arr

    def regrid(self, *args):
        return HPXPixels2D(self.pix3d, self.arr.regrid(*args))

    def subarray(self, xlim, ylim):
        return HPXPixels2D(self.pix3d, self.arr[xlim[0]:xlim[1],
                                                ylim[0]:ylim[1]])
