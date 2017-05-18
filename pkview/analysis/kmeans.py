"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, print_function, absolute_import

import sys
import time
import numpy as np
import sklearn.cluster as cl
from sklearn.decomposition import PCA

from pkview.analysis import Process

class KMeansPCAProcess(Process):
    """
    Clustering for a 4D volume
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        n_clusters = options.pop('n-clusters', 5)
        norm_data = options.pop('norm-data', True)
        n_pca = options.pop('n-pca', 5)
        reduction = options.pop('reduction', 'pca')
        invert_roi = options.pop('invert-roi', False)
        output_name = options.pop('output-name', 'clusters')
        vol_name = options.pop('vol', self.ivm.vol.name)

        img = self.ivm.overlays[vol_name].astype(np.float32)
        roi = self.ivm.current_roi

        #ROI to process
        if roi is None:
            roi = np.ones(img.shape[:-1], dtype=bool)
        elif invert_roi:
            roi = np.logical_not(roi)
        else:
            roi = roi.astype(np.bool)

        voxel_se = img[roi]
        baseline1 = np.mean(img[:, :, :, :3], axis=-1)
        baseline1sub = baseline1[roi]

        # Normalisation of the image
        voxel_se = voxel_se / (np.tile(np.expand_dims(baseline1sub, axis=-1), (1, img.shape[-1])) + 0.001) - 1

        # Outputs
        self.log = ""
        start1 = time.time()

        if reduction == 'none':
            kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)
            kmeans.fit(voxel_se)
            # self.cluster_centers_ = kmeans.cluster_centers_
        else:
            self.log += "Using PCA dimensionality reduction"
            pca = PCA(n_components=n_pca)
            reduced_data = pca.fit_transform(voxel_se)

            if norm_data:
                self.log += "Normalising PCA modes"
                min1 = np.min(reduced_data, axis=0)
                reduced_data = reduced_data - np.tile(np.expand_dims(min1, axis=0),
                                                      (reduced_data.shape[0], 1))
                max1 = np.max(reduced_data, axis=0)
                reduced_data = reduced_data / np.tile(np.expand_dims(max1, axis=0),
                                                      (reduced_data.shape[0], 1))

            kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)

            # kmeans = cl.AgglomerativeClustering(n_clusters=n_clusters)
            kmeans.fit(reduced_data)
            # converting the cluster centres back into the image feature space
            # self.cluster_centers_ = pca.inverse_transform(kmeans.cluster_centers_)

        self.log += "Elapsed time: %s" % (time.time() - start1)

        label_image = np.zeros(self.ivm.shape[:3])
        label_image[roi] = kmeans.labels_ + 1
        self.ivm.add_roi(output_name, label_image, make_current=True)

        self.status = Process.SUCCEEDED

class KMeans3DProcess(Process):
    """
    Clustering process for 3D data
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        n_clusters = options.pop('n-clusters', 5)
        invert_roi = options.pop('invert-roi', False)
        output_name = options.pop('output-name', 'overlay-clusters')
        data_name = options.pop('data', None)
        roi_name = options.pop('roi', None)
        
        # 3D data
        if data_name is not None:
            data = self.ivm.overlays[data_name].astype(np.float32)
        elif self.ivm.current_overlay is not None:
            data = self.ivm.current_overlay.astype(np.float32)
        else:
            raise RuntimeError("No data specified and no current overlay")

        if len(data.shape) != 3:
            raise RuntimeError("Can only run clustering on 3D data")
            
        # ROI to process
        if roi_name is not None:
            roi = self.ivm.rois[roi_name]
        elif self.ivm.current_roi is not None:
            roi = self.ivm.current_roi
        else:
            roi = np.ones(data.shape)
            invert_roi = False

        if invert_roi:
            roi = np.logical_not(roi)

        # Get unmasked data and cluster
        voxel_se = data[roi > 0]
        voxel_se = voxel_se[:, np.newaxis]
        kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)
        kmeans.fit(voxel_se)

        # label regions
        label_image = np.zeros_like(data, dtype=np.int)
        label_image[roi > 0] = kmeans.labels_ + 1
        self.ivm.add_roi(output_name, label_image)
        
        self.status = Process.SUCCEEDED
