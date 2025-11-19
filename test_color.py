import FreeCAD as App
import Part

try:
    doc = App.newDocument("TestColor")
    box = doc.addObject("Part::Feature", "Box")
    box.Shape = Part.makeBox(10, 10, 10)
    
    print(f"Box has ViewObject? {hasattr(box, 'ViewObject')}")
    if hasattr(box, 'ViewObject') and box.ViewObject:
        print("Setting color...")
        try:
            box.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
            print(f"Color set: {box.ViewObject.ShapeColor}")
        except Exception as e:
            print(f"Failed to set color: {e}")
    else:
        print("ViewObject is None or missing")
        
    doc.recompute()
    doc.saveAs("test_color.FCStd")
    print("Saved test_color.FCStd")
    
except Exception as e:
    print(f"Error: {e}")
