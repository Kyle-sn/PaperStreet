import com.ib.client.Decimal;
import com.paperstreet.positionhandler.PositionChecker;
import org.junit.Test;

import static org.junit.jupiter.api.Assertions.*;

public class PositionCheckerTest {

    @Test
    public void setPositionBalanceBool() {
        Decimal shareCount = Decimal.get(5d);
        PositionChecker.setPositionShareCount(shareCount);
        PositionChecker.setPositionBalanceBool();
        double positionShareCount = PositionChecker.getPositionShareCount();

        assertEquals(5d, positionShareCount);
        assertTrue(PositionChecker.getPositionBalanceBool());
    }
}
