# Copyright (c) 2008 Willow Garage, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# author: Wim Meeussen

from copy import deepcopy
from typing import Any
from typing import Callable
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union

from geometry_msgs.msg import PointStamped
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import PoseWithCovarianceStamped
from geometry_msgs.msg import TransformStamped
from geometry_msgs.msg import Vector3Stamped
from rclpy.duration import Duration
from rclpy.time import Time
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Header
import tf2_ros


MsgStamped = Union[
    PointStamped,
    PoseStamped,
    PoseWithCovarianceStamped,
    Vector3Stamped,
    PointCloud2
    ]
PyKDLType = TypeVar('PyKDLType')
TransformableObject = Union[MsgStamped, PyKDLType]
TransformableObjectType = TypeVar('TransformableObjectType')


class BufferInterface:
    """
    Abstract interface for wrapping the Python tf2 library in a ROS convenience API.

    Implementations include :class:tf2_ros.buffer.Buffer and
    :class:tf2_ros.buffer_client.BufferClient.
    """

    def __init__(self) -> None:
        self.registration = tf2_ros.TransformRegistration()

    # transform, simple api
    def transform(
        self,
        object_stamped: TransformableObject,
        target_frame: str,
        timeout: Duration = Duration(),
        new_type: Optional[TransformableObjectType] = None
    ) -> TransformableObject:
        """
        Transform an input into the target frame.

        The input must be a known transformable type (by way of the tf2 data type conversion
        interface).

        If new_type is not None, the type specified must have a valid conversion from the input
        type, else the function will raise an exception.

        :param object_stamped: The timestamped object to transform.
        :param target_frame: Name of the frame to transform the input into.
        :param timeout: Time to wait for the target frame to become available.
        :param new_type: Type to convert the object to.
        :return: The transformed, timestamped output, possibly converted to a new type.
        """
        do_transform = self.registration.get(type(object_stamped))
        res = do_transform(
            object_stamped,
            self.lookup_transform(
                target_frame, object_stamped.header.frame_id,
                object_stamped.header.stamp, timeout))
        if new_type is None:
            return res

        return convert(res, new_type)

    # transform, advanced api
    def transform_full(
        self,
        object_stamped: TransformableObject,
        target_frame: str,
        target_time: Time,
        fixed_frame: str,
        timeout: Duration = Duration(),
        new_type: Optional[TransformableObjectType] = None
    ) -> TransformableObject:
        """
        Transform an input into the target frame (advanced API).

        The input must be a known transformable type (by way of the tf2 data type conversion
        interface).

        If new_type is not None, the type specified must have a valid conversion from the input
        type, else the function will raise an exception.

        This function follows the advanced API, which allows tranforming between different time
        points, as well as specifying a frame to be considered fixed in time.

        :param object_stamped: The timestamped object to transform.
        :param target_frame: Name of the frame to transform the input into.
        :param target_time: Time to transform the input into.
        :param fixed_frame: Name of the frame to consider constant in time.
        :param timeout: Time to wait for the target frame to become available.
        :param new_type: Type to convert the object to.
        :return: The transformed, timestamped output, possibly converted to a new type.
        """
        do_transform = self.registration.get(type(object_stamped))
        res = do_transform(object_stamped, self.lookup_transform_full(
            target_frame, target_time,
            object_stamped.header.frame_id, object_stamped.header.stamp,
            fixed_frame, timeout))
        if new_type is None:
            return res

        return convert(res, new_type)

    def lookup_transform(
        self,
        target_frame: str,
        source_frame: str,
        time: Time,
        timeout: Duration = Duration()
    ) -> TransformStamped:
        """
        Get the transform from the source frame to the target frame.

        Must be implemented by a subclass of BufferInterface.

        :param target_frame: Name of the frame to transform into.
        :param source_frame: Name of the input frame.
        :param time: The time at which to get the transform (0 will get the latest).
        :param timeout: Time to wait for the target frame to become available.
        :return: The transform between the frames.
        """
        raise NotImplementedException()

    def lookup_transform_full(
        self,
        target_frame: str,
        target_time: Time,
        source_frame: str,
        source_time: Time,
        fixed_frame: str,
        timeout: Duration = Duration()
    ) -> TransformStamped:
        """
        Get the transform from the source frame to the target frame using the advanced API.

        Must be implemented by a subclass of BufferInterface.

        :param target_frame: Name of the frame to transform into.
        :param target_time: The time to transform to (0 will get the latest).
        :param source_frame: Name of the input frame.
        :param source_time: The time at which source_frame will be evaluated (0 gets the latest).
        :param fixed_frame: Name of the frame to consider constant in time.
        :param timeout: Time to wait for the target frame to become available.
        :return: The transform between the frames.
        """
        raise NotImplementedException()

    # can, simple api
    def can_transform(
        self,
        target_frame: str,
        source_frame: str,
        time: Time,
        timeout: Duration = Duration()
    ) -> bool:
        """
        Check if a transform from the source frame to the target frame is possible.

        Must be implemented by a subclass of BufferInterface.

        :param target_frame: Name of the frame to transform into.
        :param source_frame: Name of the input frame.
        :param time: The time at which to get the transform (0 will get the latest).
        :param timeout: Time to wait for the target frame to become available.
        :return: True if the transform is possible, false otherwise.
        """
        raise NotImplementedException()

    # can, advanced api
    def can_transform_full(
        self,
        target_frame: str,
        target_time: Time,
        source_frame: str,
        source_time: Time,
        fixed_frame: str,
        timeout: Duration = Duration()
    ) -> bool:
        """
        Check if a transform from the source frame to the target frame is possible (advanced API).

        Must be implemented by a subclass of BufferInterface.

        :param target_frame: Name of the frame to transform into.
        :param target_time: The time to transform to (0 will get the latest).
        :param source_frame: Name of the input frame.
        :param source_time: The time at which source_frame will be evaluated (0 gets the latest).
        :param fixed_frame: Name of the frame to consider constant in time.
        :param timeout: Time to wait for the target frame to become available.
        :return: True if the transform is possible, false otherwise.
        """
        raise NotImplementedException()


def Stamped(
    obj: TransformableObject,
    stamp: Time,
    frame_id: str
) -> TransformableObject:
    obj.header = Header(frame_id=frame_id, stamp=stamp)
    return obj


class TypeException(Exception):
    """
    The TypeException class.

    Raised when an unexpected type is received while registering a transform
    in :class:`tf2_ros.buffer_interface.BufferInterface`.
    """

    def __init__(self, errstr: str) -> None:
        self.errstr = errstr


class NotImplementedException(Exception):
    """
    The NotImplementedException class.

    Raised when can_transform or lookup_transform is not implemented in a
    subclass of :class:`tf2_ros.buffer_interface.BufferInterface`.
    """

    def __init__(self) -> None:
        self.errstr = 'CanTransform or LookupTransform not implemented'


class TransformRegistration():
    __type_map = {}

    def print_me(self) -> None:
        print(TransformRegistration.__type_map)

    def add(
        self,
        key: TransformableObjectType,
        callback: Callable[[TransformableObject, TransformStamped], TransformableObject]
    ) -> None:
        TransformRegistration.__type_map[key] = callback

    def get(
        self,
        key: TransformableObjectType
    ) -> Callable[[TransformableObject, TransformStamped], TransformableObject]:
        if key not in TransformRegistration.__type_map:
            raise TypeException('Type %s is not loaded or supported' % str(key))
        else:
            return TransformRegistration.__type_map[key]


class ConvertRegistration():
    __to_msg_map = {}
    __from_msg_map = {}
    __convert_map = {}

    def add_from_msg(
        self,
        key: TransformableObjectType,
        callback: Callable[[MsgStamped], TransformableObject]
    ) -> None:
        ConvertRegistration.__from_msg_map[key] = callback

    def add_to_msg(
        self,
        key: TransformableObjectType,
        callback: Callable[[TransformableObject], MsgStamped]
    ) -> None:
        ConvertRegistration.__to_msg_map[key] = callback

    def add_convert(
        self,
        key: Tuple[TransformableObjectType, TransformableObjectType],
        callback: Callable[[Any], TransformableObject]
    ) -> None:
        ConvertRegistration.__convert_map[key] = callback

    def get_from_msg(
        self,
        key: TransformableObjectType
    ) -> Callable[[MsgStamped], TransformableObject]:
        if key not in ConvertRegistration.__from_msg_map:
            raise TypeException('Type %s is not loaded or supported' % str(key))
        else:
            return ConvertRegistration.__from_msg_map[key]

    def get_to_msg(
        self,
        key: TransformableObjectType
    ) -> Callable[[TransformableObject], MsgStamped]:
        if key not in ConvertRegistration.__to_msg_map:
            raise TypeException('Type %s is not loaded or supported' % str(key))
        else:
            return ConvertRegistration.__to_msg_map[key]

    def get_convert(
        self,
        key: Tuple[TransformableObjectType, TransformableObjectType]
    ) -> Callable[[Any], TransformableObject]:
        if key not in ConvertRegistration.__convert_map:
            raise TypeException('Type %s is not loaded or supported' % str(key))
        else:
            return ConvertRegistration.__convert_map[key]


def convert(a: TransformableObject, b_type: TransformableObjectType) -> TransformableObject:
    c = ConvertRegistration()
    # check if an efficient conversion function between the types exists
    try:
        f = c.get_convert((type(a), b_type))
        return f(a)
    except TypeException:
        if isinstance(a, b_type):
            return deepcopy(a)

        f_to = c.get_to_msg(type(a))
        f_from = c.get_from_msg(b_type)
        return f_from(f_to(a))
