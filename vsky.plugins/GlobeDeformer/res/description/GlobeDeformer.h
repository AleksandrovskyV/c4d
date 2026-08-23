#ifndef _GlobeDeformer_H_
#define _GlobeDeformer_H_

#include "omodifier.h"

enum
{
  ID_MAIN_MODE        = 999,
  ID_AXIS_MODE        = 1000,
  ID_MULTIPLIER       = 1001,
  ID_STRENGTH         = 1002,
  ID_PROJECTION_MODE  = 1003,
  ID_LAT_SCALE        = 1004,
  
  ID_MAP_WIDTH        = 1020,
  ID_MAP_HEIGHT       = 1021,
  ID_FIT_TO_PARENT    = 1022,
  ID_GUIDE            = 1023,
  ID_UNLOCK_HEIGHT    = 1024,

  ID_PLANE_XY         = 0,
  ID_PLANE_XZ         = 1,
  ID_PLANE_ZY         = 2,

  ID_MODE_EQUID_GLOBE  = 0,
  ID_MODE_MERC_GLOBE   = 1,
  ID_MODE_EQ_TO_MERC   = 2,
  ID_MODE_MERC_TO_EQ   = 3

};

#endif
